"""Unit tests for NIfTI loader and validation."""
import io
import os
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest

from imaging.loader import NiftiLoader, load_and_validate_mri
from core.errors import (
    InvalidFileFormatError,
    CorruptedFileError,
    InvalidDimensionsError,
    GeometryValidationError,
)


def _create_synthetic_nii(
    shape=(40, 40, 20),
    spacing=(1.0, 1.0, 1.5),
    with_nan=False,
    all_zeros=False,
) -> Path:
    """Helper to create a temporary synthetic NIfTI file."""
    if all_zeros:
        data = np.zeros(shape, dtype=np.float32)
    elif with_nan:
        data = np.random.rand(*shape).astype(np.float32)
        data[5, 5, 5] = np.nan
    else:
        # Create non-trivial synthetic brain-like sphere
        data = np.random.normal(loc=100.0, scale=15.0, size=shape).astype(np.float32)
        data = np.clip(data, 0, None)
        
    affine = np.diag([spacing[0], spacing[1], spacing[2], 1.0])
    img = nib.Nifti1Image(data, affine)
    
    tmp = tempfile.NamedTemporaryFile(suffix=".nii", delete=False)
    tmp.close()
    nib.save(img, tmp.name)
    return Path(tmp.name)


def test_load_real_brats_nifti():
    """Verify loading real BraTS scan from workspace."""
    real_path = Path("BRATS/BraTS20_Training_001_flair.nii")
    if not real_path.exists():
        pytest.skip(f"Reference scan {real_path} not found in workspace.")

    raw_data, nii_img, study = NiftiLoader.load_from_path(real_path)

    assert raw_data.ndim == 3
    assert raw_data.shape == (240, 240, 155)
    assert study.dimensions.shape_tuple == (240, 240, 155)
    assert study.spacing.dx_mm == 1.0
    assert study.spacing.dy_mm == 1.0
    assert study.spacing.dz_mm == 1.0
    assert study.metadata.modality == "FLAIR"
    assert study.metadata.filename == "BraTS20_Training_001_flair.nii"
    assert study.is_valid is True
    assert len(study.orientation) == 3


def test_load_from_bytes():
    """Verify in-memory bytes upload flow (Streamlit compatibility)."""
    tmp_path = _create_synthetic_nii()
    try:
        with open(tmp_path, "rb") as f:
            file_bytes = f.read()

        raw_data, nii_img, study = NiftiLoader.load_from_bytes(
            file_bytes=file_bytes, filename="uploaded_synthetic.nii"
        )
        assert raw_data.shape == (40, 40, 20)
        assert study.dimensions.dim_x == 40
        assert study.spacing.dz_mm == 1.5
        assert study.is_valid is True
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)


def test_unsupported_extension_error():
    """Verify non-NIfTI extensions raise InvalidFileFormatError."""
    with pytest.raises(InvalidFileFormatError, match="Unsupported file format"):
        NiftiLoader.load_from_path("dummy_scan.dcm")

    with pytest.raises(InvalidFileFormatError, match="Unsupported file format"):
        NiftiLoader.load_from_bytes(b"some content", filename="scan.jpg")


def test_missing_file_error():
    """Verify non-existent paths raise CorruptedFileError."""
    with pytest.raises(CorruptedFileError, match="File not found"):
        NiftiLoader.load_from_path("non_existent_scan.nii")


def test_corrupted_file_error():
    """Verify corrupted byte content raises CorruptedFileError."""
    tmp = tempfile.NamedTemporaryFile(suffix=".nii", delete=False)
    tmp.write(b"NOT A VALID NIFTI HEADER AT ALL")
    tmp.close()
    try:
        with pytest.raises(CorruptedFileError, match="Failed to read NIfTI file"):
            NiftiLoader.load_from_path(tmp.name)
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


def test_flat_signal_error():
    """Verify zero or flat signal raises CorruptedFileError."""
    tmp_path = _create_synthetic_nii(all_zeros=True)
    try:
        with pytest.raises(CorruptedFileError, match="flat/empty signal"):
            NiftiLoader.load_from_path(tmp_path)
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)


def test_nan_voxel_error():
    """Verify NaN values trigger CorruptedFileError."""
    tmp_path = _create_synthetic_nii(with_nan=True)
    try:
        with pytest.raises(CorruptedFileError, match="non-finite"):
            NiftiLoader.load_from_path(tmp_path)
    finally:
        if tmp_path.exists():
            os.remove(tmp_path)


def test_invalid_dimensions_error():
    """Verify 2D images trigger InvalidDimensionsError."""
    data_2d = np.ones((64, 64), dtype=np.float32)
    img = nib.Nifti1Image(data_2d, np.eye(4))
    tmp = tempfile.NamedTemporaryFile(suffix=".nii", delete=False)
    tmp.close()
    nib.save(img, tmp.name)
    try:
        with pytest.raises(InvalidDimensionsError, match="Expected 3D volume"):
            NiftiLoader.load_from_path(tmp.name)
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


def test_4d_singleton_dimension_squeezed():
    """Verify 4D volume with single channel (dim 4 == 1) is safely squeezed to 3D."""
    data_4d = np.random.normal(loc=50.0, scale=10.0, size=(40, 40, 20, 1)).astype(np.float32)
    img = nib.Nifti1Image(data_4d, np.eye(4))
    tmp = tempfile.NamedTemporaryFile(suffix=".nii", delete=False)
    tmp.close()
    nib.save(img, tmp.name)
    try:
        raw_data, nii_img, study = NiftiLoader.load_from_path(tmp.name)
        assert raw_data.ndim == 3
        assert raw_data.shape == (40, 40, 20)
        assert any("Squeezed 4D singleton" in note for note in study.validation_notes)
    finally:
        del raw_data
        del nii_img
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


def test_4d_multi_channel_error():
    """Verify 4D volume with multiple channels raises InvalidDimensionsError."""
    data_4d = np.random.normal(loc=50.0, scale=10.0, size=(40, 40, 20, 4)).astype(np.float32)
    img = nib.Nifti1Image(data_4d, np.eye(4))
    tmp = tempfile.NamedTemporaryFile(suffix=".nii", delete=False)
    tmp.close()
    nib.save(img, tmp.name)
    try:
        with pytest.raises(InvalidDimensionsError, match="Expected 3D volume"):
            NiftiLoader.load_from_path(tmp.name)
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)


