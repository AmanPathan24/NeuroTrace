"""MRI volume preprocessing for model inference."""
import numpy as np
import torch


def normalize_flair(image: np.ndarray) -> np.ndarray:
    """
    Apply zero-mean, unit-variance Z-score normalization to a 3D FLAIR volume.
    Matches the exact training preprocessing of the verified NeuroSegNet model:
        flair_norm = (image - image.mean()) / (image.std() + 1e-8)
        
    Args:
        image: 3D numpy array of raw voxel intensities.
        
    Returns:
        Normalized 3D float32 numpy array.
    """
    img_float = image.astype(np.float32)
    mean_val = img_float.mean()
    std_val = img_float.std()
    
    # Avoid division by zero
    norm = (img_float - mean_val) / (std_val + 1e-8)
    return norm


def to_input_tensor(normalized_image: np.ndarray, device: str = "cpu") -> torch.Tensor:
    """
    Format a 3D normalized numpy array into a 5D PyTorch input tensor.
    
    Args:
        normalized_image: 3D numpy array of shape (D, H, W).
        device: Target execution device ('cpu' or 'cuda').
        
    Returns:
        PyTorch tensor of shape (1, 1, D, H, W) on target device.
    """
    if normalized_image.ndim != 3:
        raise ValueError(f"Expected 3D array (D, H, W), got {normalized_image.ndim}D array with shape {normalized_image.shape}")
        
    # Shape transformation: (D, H, W) -> (1, 1, D, H, W)
    tensor = torch.from_numpy(normalized_image[None, None].astype(np.float32))
    return tensor.to(device)

