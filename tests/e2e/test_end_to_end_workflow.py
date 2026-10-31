"""
End-to-End Workflow Integration Test for NeuroTrace.

Validates the full scientific pipeline:
1. Ingestion and validation of NIfTI MRI scan.
2. Inference via NeuroSegNet 3D U-Net (CPU).
3. Deterministic volumetric measurements & QC gate evaluation.
4. Interactive 2D multi-planar and 3D volumetric figure generation.
5. Gemma 4 Research Copilot evidence synthesis and chat grounding.
6. Publication-grade research PDF report generation.
7. Geometry-preserving NIfTI segmentation mask export.
"""
import io
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest
import plotly.graph_objects as go

from imaging.loader import NiftiLoader
from models.adapter import NeuroSegNetAdapter
from models.exporter import export_segmentation_nifti
from analysis.measurements import calculate_tumor_measurements
from analysis.qc import inspect_segmentation_quality
from visualization.slices_2d import (
    create_orthogonal_slice_figure,
    create_orthogonal_trio_figure,
)
from visualization.volume_3d import create_3d_volume_figure
from agents.tools import ResearchToolRegistry
from agents.copilot import GemmaResearchCopilot
from reporting.pdf_generator import generate_research_pdf_report


@pytest.fixture(scope="module")
def checkpoint_path():
    """Locate verified checkpoint."""
    ckpt = Path("Flairbased_2/model_epoch_45 (1).pt")
    if not ckpt.exists():
        pytest.skip(f"Required checkpoint {ckpt} not found.")
    return ckpt


def test_complete_research_workflow(checkpoint_path):
    """
    Execute full end-to-end pipeline on real BraTS20_Training_001_flair scan.
    """
    scan_path = Path("BRATS/BraTS20_Training_001_flair.nii")
    if not scan_path.exists():
        pytest.skip(f"Reference scan {scan_path} not found.")

    # 1. MRI Ingestion & Validation
    raw_data, nii_img, study = NiftiLoader.load_from_path(
        scan_path, study_id="BraTS20_Training_001_flair"
    )
    assert study.metadata.study_id == "BraTS20_Training_001_flair"
    assert study.metadata.filename == "BraTS20_Training_001_flair.nii"
    assert study.dimensions.dim_x == 240
    assert study.dimensions.dim_y == 240
    assert study.dimensions.dim_z == 155
    assert len(study.metadata.sha256_hash) == 64
    assert raw_data.shape == (240, 240, 155)

    # 2. Model Adapter Inference (CPU)
    adapter = NeuroSegNetAdapter(checkpoint_path=checkpoint_path, device="cpu")
    pred_mask, pred_meta = adapter.predict(raw_data, study_id=study.metadata.study_id)
    assert pred_mask.shape == (240, 240, 155)
    assert pred_mask.dtype == np.uint8
    tumor_voxels = int(np.sum(pred_mask == 1))
    assert tumor_voxels > 0, "Tumor lesion should be segmented for BraTS20_Training_001"
    assert pred_meta.inference_seconds > 0.0

    # 3. Deterministic Volumetric Measurements
    metrics = calculate_tumor_measurements(
        pred_mask=pred_mask,
        raw_volume=raw_data,
        voxel_spacing=study.spacing,
        affine=np.array(study.affine_matrix),
        study_id=study.metadata.study_id,
        prediction_id=pred_meta.prediction_id,
    )
    assert metrics.tumor_voxel_count == tumor_voxels
    assert metrics.physical_volume_cm3 > 0.0
    assert metrics.tumor_volume_fraction_percent > 0.0
    assert metrics.bounding_box is not None
    assert metrics.centroid_voxel is not None
    assert metrics.centroid_world_mm is not None
    assert metrics.ground_truth_available is False
    assert metrics.dice_score is None

    # 4. Technical Quality Control
    qc = inspect_segmentation_quality(
        pred_mask=pred_mask,
        raw_volume=raw_data,
        study_id=study.metadata.study_id,
        prediction_id=pred_meta.prediction_id,
    )
    assert qc.is_empty_mask is False
    assert qc.signal_to_noise_ratio_est > 0.0
    assert qc.contrast_ratio_est > 0.0
    assert isinstance(qc.flags, list)

    # 5. Interactive 2D & 3D Visualizations
    cz = int(metrics.centroid_voxel[2])
    fig_axial = create_orthogonal_slice_figure(
        mri_volume=raw_data,
        pred_mask=pred_mask,
        plane="axial",
        slice_idx=cz,
        show_mask=True,
        show_contours=True,
    )
    assert isinstance(fig_axial, go.Figure)

    fig_trio = create_orthogonal_trio_figure(
        mri_volume=raw_data,
        pred_mask=pred_mask,
        show_mask=True,
        show_contours=True,
    )
    assert isinstance(fig_trio, go.Figure)

    fig_3d = create_3d_volume_figure(
        mri_volume=raw_data,
        pred_mask=pred_mask,
        scale=0.15,
        show_mri=True,
        show_tumor=True,
    )
    assert isinstance(fig_3d, go.Figure)

    # 6. Gemma 4 Research Copilot & Tool Registry Grounding
    registry = ResearchToolRegistry()
    registry.register_study_session(
        study=study,
        raw_volume=raw_data,
        pred_mask=pred_mask,
        metrics=metrics,
        qc=qc,
    )

    copilot = GemmaResearchCopilot(tool_registry=registry)
    summary_text = copilot.synthesize_research_summary(study.metadata.study_id)
    assert study.metadata.study_id in summary_text
    assert f"{metrics.physical_volume_cm3:.2f} mL" in summary_text
    assert "Disclaimer" in summary_text

    chat_reply = copilot.chat("Summarize tumor volume findings", study_id=study.metadata.study_id)
    assert str(metrics.tumor_voxel_count) in chat_reply or f"{metrics.physical_volume_cm3:.2f}" in chat_reply

    # 7. PDF Report Generation & Segmentation Export
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        pdf_out = tmp_dir_path / "test_report.pdf"
        nii_out = tmp_dir_path / "test_seg.nii.gz"

        # Generate publication PDF report
        generated_pdf = generate_research_pdf_report(
            study=study,
            metrics=metrics,
            qc=qc,
            prediction_metadata=pred_meta,
            raw_volume=raw_data,
            pred_mask=pred_mask,
            ai_commentary=summary_text,
            output_path=pdf_out,
        )
        assert generated_pdf.exists()
        assert generated_pdf.stat().st_size > 30000  # ReportLab multi-page with embedded PNG slices

        # Export NIfTI segmentation mask
        exported_nii = export_segmentation_nifti(
            mask=pred_mask,
            reference_nii=nii_img,
            output_path=nii_out,
        )
        assert exported_nii.exists()

        # Reload exported NIfTI and verify geometric integrity
        loaded_nii = nib.load(exported_nii)
        loaded_data = np.asanyarray(loaded_nii.dataobj).astype(np.uint8)
        assert loaded_data.shape == (240, 240, 155)
        assert int(np.sum(loaded_data == 1)) == tumor_voxels
        assert np.allclose(loaded_nii.affine, np.array(study.affine_matrix), atol=1e-5)
        del loaded_nii, loaded_data
    del raw_data, nii_img, pred_mask, fig_axial, fig_trio, fig_3d
    import gc
    gc.collect()


def test_end_to_end_negative_synthetic_workflow():
    """
    Test edge-case workflow with an empty/negative tumor scan.
    Verifies that the entire pipeline operates robustly without crashing.
    """
    # Create synthetic brain volume (32, 32, 16) with no tumor
    synthetic_shape = (32, 32, 16)
    np.random.seed(42)
    synthetic_vol = np.random.normal(loc=100.0, scale=20.0, size=synthetic_shape).astype(np.float32)
    empty_mask = np.zeros(synthetic_shape, dtype=np.uint8)

    # Ingest synthetic image via memory stream to prevent Windows file locks
    affine = np.eye(4, dtype=np.float32)
    nii_img = nib.Nifti1Image(synthetic_vol, affine)
    nii_bytes = nii_img.to_bytes()

    raw_data, _, study = NiftiLoader.load_from_bytes(
        nii_bytes,
        filename="synthetic_negative.nii",
        study_id="study_synthetic_neg",
    )

    # Measurements on empty mask
    metrics = calculate_tumor_measurements(
        pred_mask=empty_mask,
        raw_volume=raw_data,
        voxel_spacing=study.spacing,
        affine=np.array(study.affine_matrix),
        study_id=study.metadata.study_id,
        prediction_id="pred_synthetic_neg",
    )
    assert metrics.tumor_voxel_count == 0
    assert metrics.physical_volume_cm3 == 0.0
    assert metrics.bounding_box is None
    assert metrics.centroid_voxel is None

    # QC on empty mask
    qc = inspect_segmentation_quality(
        pred_mask=empty_mask,
        raw_volume=raw_data,
        study_id=study.metadata.study_id,
        prediction_id="pred_synthetic_neg",
    )
    assert qc.is_empty_mask is True
    assert any("NEGATIVE_FINDING" in f for f in qc.flags)

    # Register and summarize
    registry = ResearchToolRegistry()
    registry.register_study_session(
        study=study,
        raw_volume=raw_data,
        pred_mask=empty_mask,
        metrics=metrics,
        qc=qc,
    )

    copilot = GemmaResearchCopilot(tool_registry=registry)
    summary = copilot.synthesize_research_summary(study.metadata.study_id)
    assert "0 voxels" in summary

    # Generate PDF report for negative scan
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_out = Path(tmp_dir) / "negative_report.pdf"
        generated_pdf = generate_research_pdf_report(
            study=study,
            metrics=metrics,
            qc=qc,
            prediction_metadata=None,
            raw_volume=raw_data,
            pred_mask=empty_mask,
            ai_commentary=summary,
            output_path=pdf_out,
        )
        assert generated_pdf.exists()
        assert generated_pdf.stat().st_size > 10000
