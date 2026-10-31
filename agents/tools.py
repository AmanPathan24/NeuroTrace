"""Allowlisted research tools registry for the Gemma 4 Research Copilot."""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
import numpy as np
import nibabel as nib

from imaging.loader import NiftiLoader
from models.adapter import NeuroSegNetAdapter
from analysis.measurements import calculate_tumor_measurements, calculate_dice_iou
from analysis.qc import inspect_segmentation_quality
from core.contracts import ValidatedStudy, AnalysisMetrics, QCReport
from core.errors import NeuroTraceError


class ResearchToolRegistry:
    """
    Allowlisted tool execution engine for the Gemma 4 AI Research Assistant.
    Enforces strict parameter validation, rejects arbitrary execution,
    and isolates MRI data locally.
    """

    def __init__(self, model_adapter: Optional[NeuroSegNetAdapter] = None):
        self.adapter = model_adapter
        # In-memory session store for multi-step research interactions
        self.studies: Dict[str, ValidatedStudy] = {}
        self.raw_volumes: Dict[str, np.ndarray] = {}
        self.masks: Dict[str, np.ndarray] = {}
        self.metrics: Dict[str, AnalysisMetrics] = {}
        self.qc_reports: Dict[str, QCReport] = {}

    def register_study_session(
        self,
        study: ValidatedStudy,
        raw_volume: np.ndarray,
        pred_mask: Optional[np.ndarray] = None,
        metrics: Optional[AnalysisMetrics] = None,
        qc: Optional[QCReport] = None,
    ) -> None:
        """Register active study data into the research session store."""
        sid = study.metadata.study_id
        self.studies[sid] = study
        self.raw_volumes[sid] = raw_volume
        if pred_mask is not None:
            self.masks[sid] = pred_mask
        if metrics is not None:
            self.metrics[sid] = metrics
        if qc is not None:
            self.qc_reports[sid] = qc

    # ================= Allowlisted Tool Implementations =================

    def validate_mri_study(self, file_path: str) -> Dict[str, Any]:
        """
        Validate an input brain MRI NIfTI file and extract verified spatial geometry.
        
        Args:
            file_path: Path to the .nii or .nii.gz file.
        """
        try:
            path = Path(file_path)
            raw_data, nii_img, study = NiftiLoader.load_from_path(path)
            self.register_study_session(study, raw_data)
            return {
                "status": "success",
                "study_id": study.metadata.study_id,
                "filename": study.metadata.filename,
                "dimensions": study.dimensions.shape_tuple,
                "voxel_spacing_mm": [
                    study.spacing.dx_mm,
                    study.spacing.dy_mm,
                    study.spacing.dz_mm,
                ],
                "orientation": study.orientation,
                "intensity_range": [
                    study.intensity_stats.min_value,
                    study.intensity_stats.max_value,
                ],
                "is_valid": study.is_valid,
                "notes": study.validation_notes,
            }
        except Exception as e:
            return {"status": "error", "error": f"Failed to validate MRI study: {e}"}

    def run_neurosegnet(self, study_id: str) -> Dict[str, Any]:
        """
        Execute deterministic 3D U-Net segmentation on an ingested MRI study.
        
        Args:
            study_id: Study identifier returned from validation.
        """
        if study_id not in self.studies or study_id not in self.raw_volumes:
            return {"status": "error", "error": f"Study '{study_id}' not found in active session."}

        try:
            if self.adapter is None:
                self.adapter = NeuroSegNetAdapter()

            raw_vol = self.raw_volumes[study_id]
            mask, metadata = self.adapter.predict(raw_vol, study_id=study_id)
            self.masks[study_id] = mask

            tumor_voxels = int(np.sum(mask == 1))
            return {
                "status": "success",
                "study_id": study_id,
                "prediction_id": metadata.prediction_id,
                "model_name": metadata.model_name,
                "checkpoint": metadata.checkpoint_file,
                "inference_seconds": metadata.inference_seconds,
                "tumor_detected": tumor_voxels > 0,
                "tumor_voxels": tumor_voxels,
            }
        except Exception as e:
            return {"status": "error", "error": f"Inference execution failed: {e}"}

    def calculate_tumor_volumes(self, study_id: str) -> Dict[str, Any]:
        """
        Calculate deterministic physical volume, bounding box, centroid, and slice distributions.
        
        Args:
            study_id: Study identifier.
        """
        if study_id not in self.studies or study_id not in self.masks:
            return {
                "status": "error",
                "error": f"Study '{study_id}' or its segmentation mask not found in active session.",
            }

        try:
            study = self.studies[study_id]
            raw_vol = self.raw_volumes[study_id]
            mask = self.masks[study_id]

            metrics = calculate_tumor_measurements(
                pred_mask=mask,
                raw_volume=raw_vol,
                voxel_spacing=study.spacing,
                affine=np.array(study.affine_matrix),
                study_id=study_id,
                prediction_id=f"pred_{study_id}",
            )
            self.metrics[study_id] = metrics

            result = {
                "status": "success",
                "study_id": study_id,
                "analysis_id": metrics.analysis_id,
                "tumor_voxel_count": metrics.tumor_voxel_count,
                "total_brain_voxels": metrics.total_brain_voxels,
                "tumor_fraction_percent": metrics.tumor_volume_fraction_percent,
                "physical_volume_cm3_mL": metrics.physical_volume_cm3,
                "ground_truth_available": metrics.ground_truth_available,
            }

            if metrics.bounding_box:
                result["bounding_box"] = {
                    "voxel_extent": metrics.bounding_box.dimensions,
                    "x_range": [metrics.bounding_box.x_min, metrics.bounding_box.x_max],
                    "y_range": [metrics.bounding_box.y_min, metrics.bounding_box.y_max],
                    "z_range": [metrics.bounding_box.z_min, metrics.bounding_box.z_max],
                }
            if metrics.centroid_voxel:
                result["centroid_voxel"] = metrics.centroid_voxel
            if metrics.centroid_world_mm:
                result["centroid_world_mm"] = metrics.centroid_world_mm
            if metrics.slice_distribution:
                result["peak_slices"] = {
                    plane: [s["slice_idx"] for s in slices[:3]]
                    for plane, slices in metrics.slice_distribution.items()
                }

            return result
        except Exception as e:
            return {"status": "error", "error": f"Volume calculation failed: {e}"}

    def inspect_segmentation_quality(self, study_id: str) -> Dict[str, Any]:
        """
        Perform automated technical QC checks on the MRI scan and segmentation mask.
        
        Args:
            study_id: Study identifier.
        """
        if study_id not in self.studies or study_id not in self.masks:
            return {"status": "error", "error": f"Study '{study_id}' or mask not found."}

        try:
            raw_vol = self.raw_volumes[study_id]
            mask = self.masks[study_id]

            qc = inspect_segmentation_quality(
                pred_mask=mask, raw_volume=raw_vol, study_id=study_id
            )
            self.qc_reports[study_id] = qc

            return {
                "status": "success",
                "qc_id": qc.qc_id,
                "is_passed": qc.is_passed,
                "is_empty_mask": qc.is_empty_mask,
                "signal_to_noise_ratio_est": qc.signal_to_noise_ratio_est,
                "contrast_ratio_est": qc.contrast_ratio_est,
                "flags": qc.flags,
            }
        except Exception as e:
            return {"status": "error", "error": f"Quality control check failed: {e}"}

    def compare_with_ground_truth(
        self, study_id: str, ground_truth_path: str
    ) -> Dict[str, Any]:
        """
        Compare segmentation mask against a provided ground-truth NIfTI mask.
        
        Args:
            study_id: Study identifier.
            ground_truth_path: Path to reference ground-truth NIfTI file.
        """
        if study_id not in self.masks:
            return {"status": "error", "error": f"Segmentation mask for study '{study_id}' not found."}

        try:
            gt_data, _, _ = NiftiLoader.load_from_path(Path(ground_truth_path))
            pred = self.masks[study_id]

            dice, iou = calculate_dice_iou(pred, gt_data)
            return {
                "status": "success",
                "study_id": study_id,
                "dice_score": dice,
                "iou_score": iou,
                "ground_truth_file": Path(ground_truth_path).name,
            }
        except Exception as e:
            return {"status": "error", "error": f"Ground-truth comparison failed: {e}"}

    def get_study_summary(self, study_id: str) -> Dict[str, Any]:
        """
        Retrieve a consolidated summary of all verified metrics and QC for a study.
        """
        if study_id not in self.studies:
            return {"status": "error", "error": f"Study '{study_id}' not found."}

        study = self.studies[study_id]
        metrics = self.metrics.get(study_id)
        qc = self.qc_reports.get(study_id)

        return {
            "status": "success",
            "study_id": study_id,
            "filename": study.metadata.filename,
            "dimensions": study.dimensions.shape_tuple,
            "voxel_spacing": [study.spacing.dx_mm, study.spacing.dy_mm, study.spacing.dz_mm],
            "metrics": metrics.model_dump() if metrics else None,
            "qc": qc.model_dump() if qc else None,
        }

    # ================= Tool Dispatcher & Schema Registry =================

    @property
    def allowlisted_tools(self) -> Dict[str, Callable]:
        """Return mapping of permitted tool names to callable methods."""
        return {
            "validate_mri_study": self.validate_mri_study,
            "run_neurosegnet": self.run_neurosegnet,
            "calculate_tumor_volumes": self.calculate_tumor_volumes,
            "inspect_segmentation_quality": self.inspect_segmentation_quality,
            "compare_with_ground_truth": self.compare_with_ground_truth,
            "get_study_summary": self.get_study_summary,
        }

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely dispatch and execute an allowlisted tool.
        Rejects arbitrary commands or unpermitted tools.
        """
        if tool_name not in self.allowlisted_tools:
            return {
                "status": "error",
                "error": f"Security violation: Tool '{tool_name}' is not permitted in NeuroTrace allowlist.",
            }

        func = self.allowlisted_tools[tool_name]
        try:
            return func(**arguments)
        except TypeError as e:
            return {"status": "error", "error": f"Invalid arguments for tool '{tool_name}': {e}"}
        except Exception as e:
            return {"status": "error", "error": f"Tool execution error: {e}"}

