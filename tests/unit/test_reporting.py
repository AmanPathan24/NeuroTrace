"""Unit tests for research PDF report generation."""
import tempfile
from pathlib import Path
import numpy as np
import pytest

from reporting.pdf_generator import generate_research_pdf_report
from imaging.loader import NiftiLoader
from analysis.measurements import calculate_tumor_measurements
from analysis.qc import inspect_segmentation_quality
from core.contracts import PredictionMetadata


@pytest.fixture
def sample_report_data():
    """Create sample study, metrics, and QC data for report generation."""
    scan_path = Path("BRATS/BraTS20_Training_001_flair.nii")
    if not scan_path.exists():
        pytest.skip(f"Reference scan {scan_path} not found.")

    raw_data, nii_img, study = NiftiLoader.load_from_path(scan_path, study_id="study_report_test")
    
    # Synthetic tumor mask
    mask = np.zeros_like(raw_data, dtype=np.uint8)
    mask[90:110, 90:110, 60:80] = 1  # 20 * 20 * 20 = 8000 voxels

    metrics = calculate_tumor_measurements(
        pred_mask=mask,
        raw_volume=raw_data,
        voxel_spacing=study.spacing,
        affine=np.array(study.affine_matrix),
        study_id=study.metadata.study_id,
        prediction_id="pred_report_test",
    )
    qc = inspect_segmentation_quality(mask, raw_data, study_id=study.metadata.study_id)
    pred_meta = PredictionMetadata(
        prediction_id="pred_report_test",
        study_id=study.metadata.study_id,
        model_name="NeuroSegNet 3D U-Net",
        checkpoint_file="model_epoch_45 (1).pt",
        checkpoint_hash="75d01bb02b5abc342259ed24016925ba07ed93ddc2ddb181468788cef3fd9f39",
        device="cpu",
        inference_seconds=12.50,
    )

    return study, metrics, qc, pred_meta, raw_data, mask


def test_generate_pdf_report_with_images(sample_report_data):
    """Verify PDF report generation with embedded multi-planar figures."""
    study, metrics, qc, pred_meta, raw_data, mask = sample_report_data

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_pdf = Path(tmp_dir) / "test_report.pdf"
        pdf_path = generate_research_pdf_report(
            study=study,
            metrics=metrics,
            qc=qc,
            prediction_metadata=pred_meta,
            ai_commentary="Automated test commentary verifying deterministic metrics.",
            raw_volume=raw_data,
            pred_mask=mask,
            output_path=out_pdf,
        )

        assert pdf_path.exists()
        file_size = pdf_path.stat().st_size
        assert file_size > 10000  # Report with embedded figures should be > 10 KB

        # Verify PDF header signature
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            assert header == b"%PDF-"


def test_generate_pdf_report_without_images(sample_report_data):
    """Verify PDF report generation when raw volume is omitted."""
    study, metrics, qc, pred_meta, _, _ = sample_report_data

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_pdf = Path(tmp_dir) / "test_report_no_img.pdf"
        pdf_path = generate_research_pdf_report(
            study=study,
            metrics=metrics,
            qc=qc,
            prediction_metadata=pred_meta,
            raw_volume=None,
            pred_mask=None,
            output_path=out_pdf,
        )

        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 3000

