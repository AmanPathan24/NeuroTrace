"""Deterministic quantitative segmentation measurements and spatial geometry analysis."""
import uuid
from typing import Optional, Dict, List, Tuple, Any
import numpy as np
import nibabel as nib

from core.contracts import (
    AnalysisMetrics,
    BoundingBox3D,
    VoxelSpacing,
)
from core.errors import GeometryValidationError


def calculate_dice_iou(
    pred_mask: np.ndarray, ground_truth_mask: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate deterministic Dice Similarity Coefficient and Intersection-over-Union (IoU).
    
    Args:
        pred_mask: Binary prediction mask (0 and 1).
        ground_truth_mask: Binary reference ground-truth mask (0 and 1).
        
    Returns:
        Tuple of (dice_score, iou_score).
    """
    if pred_mask.shape != ground_truth_mask.shape:
        raise GeometryValidationError(
            f"Shape mismatch: prediction mask {pred_mask.shape} != ground truth {ground_truth_mask.shape}"
        )

    p_bin = (pred_mask > 0).astype(np.bool_)
    g_bin = (ground_truth_mask > 0).astype(np.bool_)

    intersection = np.logical_and(p_bin, g_bin).sum()
    p_sum = p_bin.sum()
    g_sum = g_bin.sum()
    union = np.logical_or(p_bin, g_bin).sum()

    if p_sum == 0 and g_sum == 0:
        # Both empty: perfect agreement on negative finding
        return 1.0, 1.0

    dice = float((2.0 * intersection) / (p_sum + g_sum))
    iou = float(intersection / union) if union > 0 else 0.0

    return round(dice, 4), round(iou, 4)


def extract_slice_distribution(
    pred_mask: np.ndarray, top_k: int = 5
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate slice-wise tumor voxel distribution along Axial, Coronal, and Sagittal axes.
    Identifies key diagnostic slices with peak tumor involvement.
    
    Args:
        pred_mask: 3D binary segmentation mask.
        top_k: Number of highest-involvement slices to report per anatomical plane.
        
    Returns:
        Dictionary mapping axis ('axial', 'coronal', 'sagittal') to list of top slice records.
    """
    total_tumor_voxels = int(np.sum(pred_mask > 0))
    if total_tumor_voxels == 0:
        return {"axial": [], "coronal": [], "sagittal": []}

    dim_x, dim_y, dim_z = pred_mask.shape
    distribution = {}

    # 1. Axial slices (along Z axis)
    axial_counts = [int(np.sum(pred_mask[:, :, z] > 0)) for z in range(dim_z)]
    axial_ranked = sorted(
        [
            {
                "axis": "axial",
                "slice_idx": z,
                "tumor_voxels": count,
                "tumor_fraction_of_lesion": round((count / total_tumor_voxels) * 100.0, 2),
            }
            for z, count in enumerate(axial_counts)
            if count > 0
        ],
        key=lambda x: x["tumor_voxels"],
        reverse=True,
    )
    distribution["axial"] = axial_ranked[:top_k]

    # 2. Coronal slices (along Y axis)
    coronal_counts = [int(np.sum(pred_mask[:, y, :] > 0)) for y in range(dim_y)]
    coronal_ranked = sorted(
        [
            {
                "axis": "coronal",
                "slice_idx": y,
                "tumor_voxels": count,
                "tumor_fraction_of_lesion": round((count / total_tumor_voxels) * 100.0, 2),
            }
            for y, count in enumerate(coronal_counts)
            if count > 0
        ],
        key=lambda x: x["tumor_voxels"],
        reverse=True,
    )
    distribution["coronal"] = coronal_ranked[:top_k]

    # 3. Sagittal slices (along X axis)
    sagittal_counts = [int(np.sum(pred_mask[x, :, :] > 0)) for x in range(dim_x)]
    sagittal_ranked = sorted(
        [
            {
                "axis": "sagittal",
                "slice_idx": x,
                "tumor_voxels": count,
                "tumor_fraction_of_lesion": round((count / total_tumor_voxels) * 100.0, 2),
            }
            for x, count in enumerate(sagittal_counts)
            if count > 0
        ],
        key=lambda x: x["tumor_voxels"],
        reverse=True,
    )
    distribution["sagittal"] = sagittal_ranked[:top_k]

    return distribution


def calculate_tumor_measurements(
    pred_mask: np.ndarray,
    raw_volume: np.ndarray,
    voxel_spacing: VoxelSpacing,
    affine: np.ndarray,
    study_id: str,
    prediction_id: str,
    ground_truth_mask: Optional[np.ndarray] = None,
) -> AnalysisMetrics:
    """
    Compute rigorous deterministic quantitative tumor measurements from binary segmentation.
    
    Args:
        pred_mask: 3D binary segmentation mask array.
        raw_volume: 3D raw MRI voxel intensity array.
        voxel_spacing: VoxelSpacing contract containing dx, dy, dz in mm.
        affine: 4x4 spatial affine coordinate matrix.
        study_id: Identifier of the analyzed study.
        prediction_id: Identifier of the segmentation inference run.
        ground_truth_mask: Optional reference ground-truth mask.
        
    Returns:
        AnalysisMetrics Pydantic contract populated with verifiable metrics.
    """
    if pred_mask.shape != raw_volume.shape:
        raise GeometryValidationError(
            f"Dimension mismatch between prediction mask {pred_mask.shape} and raw volume {raw_volume.shape}"
        )

    # 1. Deterministic voxel counts
    tumor_voxel_count = int(np.sum(pred_mask == 1))
    
    # Brain tissue voxels (non-air voxels with intensity > 0)
    total_brain_voxels = int(np.sum(raw_volume > 0))
    
    tumor_volume_fraction = (
        round((tumor_voxel_count / total_brain_voxels) * 100.0, 3)
        if total_brain_voxels > 0
        else 0.0
    )

    # 2. Physical volume calculation using verified voxel dimensions:
    # Physical Volume (mL or cm^3) = (voxels * mm^3 per voxel) / 1000.0
    voxel_vol_mm3 = voxel_spacing.voxel_volume_mm3
    physical_volume_cm3 = round((tumor_voxel_count * voxel_vol_mm3) / 1000.0, 3)

    bounding_box = None
    centroid_voxel = None
    centroid_world_mm = None

    if tumor_voxel_count > 0:
        # 3. 3D Bounding box
        indices = np.where(pred_mask == 1)
        x_min, x_max = int(indices[0].min()), int(indices[0].max())
        y_min, y_max = int(indices[1].min()), int(indices[1].max())
        z_min, z_max = int(indices[2].min()), int(indices[2].max())

        bounding_box = BoundingBox3D(
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
            z_min=z_min,
            z_max=z_max,
        )

        # 4. Centroid in voxel index coordinates
        c_x = float(np.mean(indices[0]))
        c_y = float(np.mean(indices[1]))
        c_z = float(np.mean(indices[2]))
        centroid_voxel = (round(c_x, 2), round(c_y, 2), round(c_z, 2))

        # 5. Centroid in physical scanner coordinates (mm) via affine transformation
        world_pt = nib.affines.apply_affine(affine, [c_x, c_y, c_z])
        centroid_world_mm = (
            round(float(world_pt[0]), 2),
            round(float(world_pt[1]), 2),
            round(float(world_pt[2]), 2),
        )

    # 6. Slice distribution
    slice_distribution = extract_slice_distribution(pred_mask)

    # 7. Ground truth evaluation (strictly optional)
    gt_available = False
    dice = None
    iou = None

    if ground_truth_mask is not None:
        dice, iou = calculate_dice_iou(pred_mask, ground_truth_mask)
        gt_available = True

    analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"

    return AnalysisMetrics(
        analysis_id=analysis_id,
        study_id=study_id,
        prediction_id=prediction_id,
        tumor_voxel_count=tumor_voxel_count,
        total_brain_voxels=total_brain_voxels,
        tumor_volume_fraction_percent=tumor_volume_fraction,
        physical_volume_cm3=physical_volume_cm3,
        bounding_box=bounding_box,
        centroid_voxel=centroid_voxel,
        centroid_world_mm=centroid_world_mm,
        slice_distribution=slice_distribution,
        ground_truth_available=gt_available,
        dice_score=dice,
        iou_score=iou,
    )

