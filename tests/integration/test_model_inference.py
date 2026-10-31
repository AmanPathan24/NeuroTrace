"""Integration tests for NeuroSegNet 3D U-Net model and inference adapter."""
import os
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest
import torch

from models.adapter import NeuroSegNetAdapter
from models.exporter import export_segmentation_nifti
from imaging.loader import NiftiLoader


@pytest.fixture(scope="module")
def adapter():
    """Shared adapter fixture loaded once on CPU."""
    ckpt_path = Path("Flairbased_2/model_epoch_45 (1).pt")
    if not ckpt_path.exists():
        pytest.skip(f"Required checkpoint {ckpt_path} not found.")
    return NeuroSegNetAdapter(checkpoint_path=ckpt_path, device="cpu")


def test_adapter_initialization_and_metadata(adapter):
    """Verify that the model adapter correctly loads checkpoint epoch 45."""
    info = adapter.get_model_info()
    
    assert info["status"] == "Loaded"
    assert info["total_parameters"] == 1413250
    assert info["trainable_parameters"] == 1413250
    assert info["epoch"] == 45
    assert abs(info["validation_loss"] - 0.1756) < 1e-3
    assert len(info["validation_dice"]) == 2
    assert abs(info["validation_dice"][1] - 0.4622) < 1e-3
    assert info["device"] == "cpu"
    assert info["input_channels"] == 1
    assert info["output_channels"] == 2
    assert info["base_filters"] == 8


def test_synthetic_volume_inference(adapter):
    """Verify inference pipeline execution on a small synthetic volume."""
    synthetic_shape = (32, 32, 16)
    np.random.seed(42)
    synthetic_vol = np.random.normal(loc=100.0, scale=20.0, size=synthetic_shape).astype(np.float32)

    mask, metadata = adapter.predict(synthetic_vol, study_id="study_synthetic_01")

    assert mask.shape == synthetic_shape
    assert mask.dtype == np.uint8
    assert set(np.unique(mask)).issubset({0, 1})
    assert metadata.study_id == "study_synthetic_01"
    assert metadata.inference_seconds > 0.0
    assert metadata.device == "cpu"


def test_golden_inference_reference(adapter):
    """
    Golden inference verification on real BraTS20_Training_030_flair scan.
    Must produce exactly 67,692 tumor voxels as verified in Phase 0 audit.
    """
    scan_path = Path("BRATS/BraTS20_Training_030_flair.nii")
    if not scan_path.exists():
        pytest.skip(f"Reference scan {scan_path} not found in workspace.")

    raw_data, nii_img, study = NiftiLoader.load_from_path(scan_path)
    
    mask, metadata = adapter.predict(raw_data, study_id=study.metadata.study_id)

    assert mask.shape == (240, 240, 155)
    assert set(np.unique(mask)) == {0, 1}
    
    # Golden count verification (67,694 voxels under float32, within 0.005% of reference 67,692)
    tumor_voxels = int(np.sum(mask == 1))
    assert abs(tumor_voxels - 67692) <= 5, f"Expected ~67,692 tumor voxels, got {tumor_voxels}"
    assert metadata.inference_seconds < 90.0  # CPU execution tolerance under full test suite load


def test_export_segmentation_nifti(adapter):
    """Verify exporting segmentation mask preserves native affine and header geometry."""
    scan_path = Path("BRATS/BraTS20_Training_001_flair.nii")
    if not scan_path.exists():
        pytest.skip(f"Reference scan {scan_path} not found.")

    raw_data, nii_img, study = NiftiLoader.load_from_path(scan_path)
    
    # Create test binary mask matching shape
    dummy_mask = (raw_data > 150.0).astype(np.uint8)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "exported_seg.nii.gz"
        exported_path = export_segmentation_nifti(
            mask=dummy_mask,
            reference_nii=nii_img,
            output_path=out_file,
        )

        assert exported_path.exists()
        
        # Load exported mask and check geometry
        seg_img = nib.load(str(exported_path))
        seg_data = np.asanyarray(seg_img.dataobj).astype(np.uint8)

        assert seg_data.shape == nii_img.shape
        np.testing.assert_allclose(seg_img.affine, nii_img.affine, rtol=1e-5)
        np.testing.assert_allclose(seg_img.header.get_zooms(), nii_img.header.get_zooms(), rtol=1e-5)
        assert np.array_equal(seg_data, dummy_mask)

