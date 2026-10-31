"""Unit tests for deterministic analysis measurements and QC checks."""
import numpy as np
import pytest

from analysis.measurements import (
    calculate_tumor_measurements,
    calculate_dice_iou,
    extract_slice_distribution,
)
from analysis.qc import inspect_segmentation_quality
from core.contracts import VoxelSpacing


def test_known_cube_volume_and_centroid():
    """
    Verify volume, bounding box, and centroid calculation on a synthetic 10x10x10 cube.
    Volume: 1000 voxels.
    Spacing: (2.0, 2.0, 2.0) mm -> 8.0 mm^3 per voxel.
    Physical volume: 1000 * 8.0 / 1000 = 8.000 cm^3 (mL).
    """
    grid_size = 50
    mask = np.zeros((grid_size, grid_size, grid_size), dtype=np.uint8)
    raw = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)

    # Place brain tissue in center (40x40x40)
    raw[5:45, 5:45, 5:45] = 100.0

    # Place cube tumor at [20:30, 20:30, 20:30]
    mask[20:30, 20:30, 20:30] = 1
    raw[20:30, 20:30, 20:30] = 200.0  # Hyperintense lesion

    spacing = VoxelSpacing(dx_mm=2.0, dy_mm=2.0, dz_mm=2.0)
    affine = np.diag([2.0, 2.0, 2.0, 1.0])

    metrics = calculate_tumor_measurements(
        pred_mask=mask,
        raw_volume=raw,
        voxel_spacing=spacing,
        affine=affine,
        study_id="study_cube_01",
        prediction_id="pred_cube_01",
    )

    assert metrics.tumor_voxel_count == 1000
    assert metrics.physical_volume_cm3 == 8.0
    assert metrics.bounding_box is not None
    assert metrics.bounding_box.x_min == 20
    assert metrics.bounding_box.x_max == 29
    assert metrics.bounding_box.y_min == 20
    assert metrics.bounding_box.y_max == 29
    assert metrics.bounding_box.z_min == 20
    assert metrics.bounding_box.z_max == 29
    assert metrics.bounding_box.dimensions == (10, 10, 10)

    # Centroid in voxel index is 24.5, 24.5, 24.5
    assert metrics.centroid_voxel == (24.5, 24.5, 24.5)
    # World coordinate = 24.5 * 2.0 = 49.0 mm
    assert metrics.centroid_world_mm == (49.0, 49.0, 49.0)

    # Missing ground truth must be reported as None/False
    assert metrics.ground_truth_available is False
    assert metrics.dice_score is None
    assert metrics.iou_score is None


def test_missing_ground_truth_handling():
    """Verify missing ground truth is strictly reported as unavailable, never 0 or fake."""
    mask = np.ones((10, 10, 10), dtype=np.uint8)
    raw = np.ones((10, 10, 10), dtype=np.float32)
    spacing = VoxelSpacing(dx_mm=1.0, dy_mm=1.0, dz_mm=1.0)
    affine = np.eye(4)

    metrics = calculate_tumor_measurements(
        pred_mask=mask,
        raw_volume=raw,
        voxel_spacing=spacing,
        affine=affine,
        study_id="study_no_gt",
        prediction_id="pred_no_gt",
        ground_truth_mask=None,
    )

    assert metrics.ground_truth_available is False
    assert metrics.dice_score is None
    assert metrics.iou_score is None


def test_dice_and_iou_calculation():
    """Verify Dice and IoU on known overlapping masks."""
    m1 = np.zeros((10, 10, 10), dtype=np.uint8)
    m2 = np.zeros((10, 10, 10), dtype=np.uint8)

    # 1. Identical masks
    m1[2:6, 2:6, 2:6] = 1
    m2[2:6, 2:6, 2:6] = 1
    dice, iou = calculate_dice_iou(m1, m2)
    assert dice == 1.0
    assert iou == 1.0

    # 2. Completely disjoint masks
    m3 = np.zeros((10, 10, 10), dtype=np.uint8)
    m3[7:9, 7:9, 7:9] = 1
    dice_disjoint, iou_disjoint = calculate_dice_iou(m1, m3)
    assert dice_disjoint == 0.0
    assert iou_disjoint == 0.0

    # 3. 50% intersection
    # m1 has 64 voxels (4x4x4)
    # m4 shares half of m1 (32 voxels) and has 32 disjoint voxels (total 64)
    m4 = np.zeros((10, 10, 10), dtype=np.uint8)
    m4[2:4, 2:6, 2:6] = 1  # 2 * 4 * 4 = 32 voxels overlap
    m4[0:2, 2:6, 2:6] = 1  # 32 extra voxels
    d, j = calculate_dice_iou(m1, m4)
    # Dice = 2*32 / (64 + 64) = 64/128 = 0.5
    # IoU = 32 / (64 + 64 - 32) = 32 / 96 = 0.3333
    assert abs(d - 0.5) < 1e-3
    assert abs(j - 0.3333) < 1e-3


def test_slice_distribution():
    """Verify top diagnostic slices are extracted and ranked."""
    mask = np.zeros((20, 20, 20), dtype=np.uint8)
    # Slice z=5 has 4 voxels
    mask[2:4, 2:4, 5] = 1
    # Slice z=10 has 16 voxels (peak)
    mask[2:6, 2:6, 10] = 1

    dist = extract_slice_distribution(mask, top_k=2)
    assert len(dist["axial"]) == 2
    assert dist["axial"][0]["slice_idx"] == 10
    assert dist["axial"][0]["tumor_voxels"] == 16
    assert dist["axial"][1]["slice_idx"] == 5
    assert dist["axial"][1]["tumor_voxels"] == 4


def test_qc_empty_mask_check():
    """Verify QC flags negative findings on empty masks."""
    empty_mask = np.zeros((30, 30, 30), dtype=np.uint8)
    raw = np.ones((30, 30, 30), dtype=np.float32) * 50.0

    qc = inspect_segmentation_quality(empty_mask, raw, study_id="study_empty")
    assert qc.is_empty_mask is True
    assert any("NEGATIVE_FINDING" in f for f in qc.flags)


def test_qc_boundary_overflow_and_components():
    """Verify QC detects air-boundary overflow and multiple components."""
    mask = np.zeros((40, 40, 40), dtype=np.uint8)
    raw = np.zeros((40, 40, 40), dtype=np.float32)

    # Brain is only at [10:30, 10:30, 10:30]
    raw[10:30, 10:30, 10:30] = 100.0

    # Cluster 1 inside brain
    mask[15:18, 15:18, 15:18] = 1
    # Cluster 2 outside brain (in air at [2:4, 2:4, 2:4])
    mask[2:4, 2:4, 2:4] = 1

    qc = inspect_segmentation_quality(mask, raw, study_id="study_multi")
    assert qc.is_empty_mask is False
    assert any("AIR_BOUNDARY_OVERFLOW" in f for f in qc.flags)
    assert any("MULTI_COMPONENT_SEGMENTATION" in f for f in qc.flags)

