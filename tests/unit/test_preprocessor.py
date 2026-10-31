"""Unit tests for imaging preprocessor."""
import numpy as np
import torch
import pytest

from imaging.preprocessor import normalize_flair, to_input_tensor


def test_normalize_flair_statistics():
    """Verify Z-score normalization produces zero mean and unit variance."""
    np.random.seed(42)
    sample_vol = np.random.normal(loc=120.0, scale=35.0, size=(30, 30, 20)).astype(np.float32)
    
    norm_vol = normalize_flair(sample_vol)
    
    assert norm_vol.shape == sample_vol.shape
    assert norm_vol.dtype == np.float32
    assert abs(norm_vol.mean()) < 1e-4
    assert abs(norm_vol.std() - 1.0) < 1e-4


def test_to_input_tensor_shape_and_type():
    """Verify conversion to PyTorch 5D input tensor."""
    arr = np.zeros((240, 240, 155), dtype=np.float32)
    tensor = to_input_tensor(arr, device="cpu")
    
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == torch.Size([1, 1, 240, 240, 155])
    assert tensor.dtype == torch.float32
    assert tensor.device == torch.device("cpu")


def test_to_input_tensor_invalid_dimension():
    """Verify non-3D array triggers ValueError."""
    arr_2d = np.zeros((100, 100), dtype=np.float32)
    with pytest.raises(ValueError, match="Expected 3D array"):
        to_input_tensor(arr_2d)

