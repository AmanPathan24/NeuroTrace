"""Automated technical Quality Control checks for MRI and segmentations."""
import uuid
from typing import List, Tuple
import numpy as np
from scipy.ndimage import label

from core.contracts import QCReport


def inspect_segmentation_quality(
    pred_mask: np.ndarray,
    raw_volume: np.ndarray,
    study_id: str,
    prediction_id: str = "pred_unknown",
) -> QCReport:
    """
    Perform automated technical quality control checks on an MRI scan and its segmentation.
    
    Checks performed:
    1. Empty mask evaluation (negative vs positive finding).
    2. Brain tissue coverage and boundary integrity (checks if segmented voxels lie in air).
    3. Multi-focal lesion / component connectivity analysis.
    4. Image Signal-to-Noise Ratio (SNR) estimation.
    5. Tumor-to-parenchyma contrast ratio estimation.
    
    Args:
        pred_mask: 3D binary segmentation mask array.
        raw_volume: 3D raw MRI voxel intensity array.
        study_id: Study identifier.
        prediction_id: Prediction run identifier.
        
    Returns:
        QCReport Pydantic schema with quality metrics and technical flags.
    """
    flags: List[str] = []
    tumor_voxels = int(np.sum(pred_mask == 1))
    total_voxels = raw_volume.size
    brain_mask = raw_volume > 0
    brain_voxels = int(np.sum(brain_mask))
    brain_fraction = float(brain_voxels / total_voxels) if total_voxels > 0 else 0.0

    is_empty = tumor_voxels == 0
    if is_empty:
        flags.append("NEGATIVE_FINDING: Zero tumor voxels segmented across the entire volume.")

    # 1. Boundary / Air-space check
    boundary_overflow_count = 0
    if not is_empty:
        overflow_mask = (pred_mask == 1) & (~brain_mask)
        boundary_overflow_count = int(np.sum(overflow_mask))
        if boundary_overflow_count > 0:
            overflow_fraction = (boundary_overflow_count / tumor_voxels) * 100.0
            flags.append(
                f"AIR_BOUNDARY_OVERFLOW: {boundary_overflow_count} tumor voxels ({overflow_fraction:.2f}%) "
                f"detected outside the apparent brain boundary."
            )

    # 2. Connected Component Analysis (Multi-focality / Fragmentation)
    num_components = 0
    if not is_empty:
        labeled_mask, num_components = label(pred_mask == 1)
        if num_components > 1:
            component_sizes = [
                int(np.sum(labeled_mask == c)) for c in range(1, num_components + 1)
            ]
            primary_size = max(component_sizes)
            primary_ratio = (primary_size / tumor_voxels) * 100.0
            flags.append(
                f"MULTI_COMPONENT_SEGMENTATION: {num_components} distinct lesion components detected. "
                f"Primary component comprises {primary_ratio:.1f}% of total segmented volume."
            )

    # 3. SNR (Signal-to-Noise Ratio) Estimation
    # Background is air voxels (raw_volume <= 0 or near 0)
    bg_voxels = raw_volume[raw_volume <= 0]
    if len(bg_voxels) > 100:
        bg_noise = float(np.std(bg_voxels))
    else:
        # Fallback to lowest 10th percentile for noise estimation
        p10 = float(np.percentile(raw_volume, 10))
        low_noise = raw_volume[raw_volume <= p10]
        bg_noise = float(np.std(low_noise))

    fg_signal = float(np.mean(raw_volume[brain_mask])) if brain_voxels > 0 else 0.0
    snr_est = round(fg_signal / (bg_noise + 1e-4), 2)

    # 4. Contrast Ratio: Mean tumor intensity vs Mean normal brain intensity
    contrast_ratio = 1.0
    if not is_empty and brain_voxels > tumor_voxels:
        tumor_mean = float(np.mean(raw_volume[pred_mask == 1]))
        normal_brain_mask = brain_mask & (pred_mask == 0)
        normal_mean = (
            float(np.mean(raw_volume[normal_brain_mask]))
            if np.sum(normal_brain_mask) > 0
            else 1.0
        )
        contrast_ratio = round(tumor_mean / (normal_mean + 1e-4), 3)

    # 5. Quality evaluation gate: Pass if no severe overflow or flat SNR
    is_passed = True
    if boundary_overflow_count > (tumor_voxels * 0.10) and tumor_voxels > 100:
        is_passed = False
        flags.append("CRITICAL_QC_FAIL: Over 10% of tumor voxels reside outside brain tissue.")
    elif snr_est < 1.0:
        is_passed = False
        flags.append("CRITICAL_QC_FAIL: Abnormally low signal-to-noise ratio in input scan.")

    qc_id = f"qc_{uuid.uuid4().hex[:8]}"

    return QCReport(
        qc_id=qc_id,
        study_id=study_id,
        prediction_id=prediction_id,
        is_empty_mask=is_empty,
        brain_voxel_fraction=round(brain_fraction, 4),
        signal_to_noise_ratio_est=snr_est,
        contrast_ratio_est=contrast_ratio,
        is_passed=is_passed,
        flags=flags,
    )

