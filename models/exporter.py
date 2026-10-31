"""Export utilities for segmentation masks preserving spatial geometry."""
from pathlib import Path
from typing import Union
import numpy as np
import nibabel as nib

from core.errors import GeometryValidationError


def export_segmentation_nifti(
    mask: np.ndarray,
    reference_nii: nib.Nifti1Image,
    output_path: Union[str, Path],
) -> Path:
    """
    Export a binary segmentation mask to a NIfTI file, rigorously preserving
    the exact affine coordinate transformation matrix and spatial header from
    the reference MRI scan.
    
    Args:
        mask: 3D numpy array containing binary segmentation labels {0, 1}.
        reference_nii: Original input nibabel Nifti1Image providing spatial geometry.
        output_path: Destination path for the exported .nii or .nii.gz file.
        
    Returns:
        Resolved Path to the saved NIfTI segmentation mask.
    """
    out_path = Path(output_path)
    if mask.shape != reference_nii.shape:
        raise GeometryValidationError(
            f"Segmentation mask shape {mask.shape} does not match reference MRI shape {reference_nii.shape}."
        )

    # Ensure parent directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Clone header and set datatype to uint8
    new_header = reference_nii.header.copy()
    new_header.set_data_dtype(np.uint8)

    # Create new spatial image preserving affine
    seg_nii = nib.Nifti1Image(
        dataobj=mask.astype(np.uint8),
        affine=reference_nii.affine,
        header=new_header,
    )

    nib.save(seg_nii, str(out_path))
    return out_path.resolve()

