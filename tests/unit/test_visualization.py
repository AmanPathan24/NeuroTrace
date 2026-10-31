"""Unit tests for 2D and 3D visualization components."""
import numpy as np
import plotly.graph_objects as go
import pytest

from visualization.slices_2d import (
    normalize_slice_display,
    create_orthogonal_slice_figure,
    create_orthogonal_trio_figure,
    extract_plane_slice,
)
from visualization.volume_3d import create_3d_volume_figure


@pytest.fixture
def sample_volumes():
    """Create a sample 3D MRI volume and tumor mask."""
    shape = (40, 40, 30)
    mri = np.random.normal(loc=100.0, scale=20.0, size=shape).astype(np.float32)
    mri = np.clip(mri, 0, None)
    
    # Brain tissue mask in center
    mask = np.zeros(shape, dtype=np.uint8)
    mask[15:25, 15:25, 10:20] = 1
    mri[mask == 1] += 80.0  # Hyperintense tumor region
    
    return mri, mask


def test_normalize_slice_display():
    """Verify 2D slice normalization produces range [0, 1]."""
    slice2d = np.array([[10.0, 50.0], [100.0, 200.0]], dtype=np.float32)
    norm = normalize_slice_display(slice2d)
    assert norm.min() >= 0.0
    assert norm.max() <= 1.0
    assert norm.dtype == np.float32

    # Flat array should not divide by zero
    flat = np.ones((5, 5), dtype=np.float32) * 42.0
    flat_norm = normalize_slice_display(flat)
    assert not np.isnan(flat_norm).any()


def test_create_orthogonal_slice_figure_axial(sample_volumes):
    """Verify Plotly axial slice figure with overlay and contours."""
    mri, mask = sample_volumes
    fig = create_orthogonal_slice_figure(
        mri_volume=mri,
        pred_mask=mask,
        plane="axial",
        slice_idx=15,
        show_mask=True,
        show_contours=True,
    )

    assert isinstance(fig, go.Figure)
    trace_types = [type(t) for t in fig.data]
    assert go.Heatmap in trace_types
    assert go.Scatter in trace_types  # Contours
    
    # Check orientation labels
    text_annotations = [a.text for a in fig.layout.annotations]
    assert any("Anterior" in t for t in text_annotations)
    assert any("Posterior" in t for t in text_annotations)


def test_create_orthogonal_slice_figure_coronal_and_sagittal(sample_volumes):
    """Verify Coronal and Sagittal views."""
    mri, mask = sample_volumes

    fig_cor = create_orthogonal_slice_figure(
        mri_volume=mri, pred_mask=mask, plane="coronal", slice_idx=20
    )
    assert isinstance(fig_cor, go.Figure)
    assert any("Superior" in a.text for a in fig_cor.layout.annotations)

    fig_sag = create_orthogonal_slice_figure(
        mri_volume=mri, pred_mask=mask, plane="sagittal", slice_idx=20
    )
    assert isinstance(fig_sag, go.Figure)
    assert any("Superior" in a.text for a in fig_sag.layout.annotations)


def test_create_orthogonal_trio_figure(sample_volumes):
    """Verify 3-panel synchronized figure."""
    mri, mask = sample_volumes
    fig = create_orthogonal_trio_figure(
        mri_volume=mri,
        pred_mask=mask,
        axial_idx=15,
        coronal_idx=20,
        sagittal_idx=20,
        show_mask=True,
    )
    assert isinstance(fig, go.Figure)
    # Must contain traces for each panel
    assert len(fig.data) >= 3


def test_create_3d_volume_figure_full(sample_volumes):
    """Verify 3D volume figure contains both go.Volume and go.Isosurface traces."""
    mri, mask = sample_volumes
    fig = create_3d_volume_figure(
        mri_volume=mri,
        pred_mask=mask,
        scale=0.25,
        show_mri=True,
        show_tumor=True,
    )

    assert isinstance(fig, go.Figure)
    trace_types = [type(t) for t in fig.data]
    assert go.Volume in trace_types
    assert go.Isosurface in trace_types


def test_create_3d_volume_figure_visibility_toggles(sample_volumes):
    """Verify independent visibility controls for brain volume and tumor surface."""
    mri, mask = sample_volumes

    # Hide MRI, show tumor only
    fig_tumor_only = create_3d_volume_figure(
        mri_volume=mri,
        pred_mask=mask,
        show_mri=False,
        show_tumor=True,
    )
    types_tumor_only = [type(t) for t in fig_tumor_only.data]
    assert go.Volume not in types_tumor_only
    assert go.Isosurface in types_tumor_only

    # Show MRI, hide tumor
    fig_mri_only = create_3d_volume_figure(
        mri_volume=mri,
        pred_mask=mask,
        show_mri=True,
        show_tumor=False,
    )
    types_mri_only = [type(t) for t in fig_mri_only.data]
    assert go.Volume in types_mri_only
    assert go.Isosurface not in types_mri_only


def test_create_3d_volume_empty_mask(sample_volumes):
    """Verify 3D figure handles empty/negative tumor masks gracefully."""
    mri, _ = sample_volumes
    empty_mask = np.zeros_like(mri, dtype=np.uint8)

    fig = create_3d_volume_figure(
        mri_volume=mri,
        pred_mask=empty_mask,
        show_mri=True,
        show_tumor=True,
    )
    assert isinstance(fig, go.Figure)
    trace_types = [type(t) for t in fig.data]
    assert go.Volume in trace_types
    assert go.Isosurface not in trace_types  # Gracefully omitted when mask is empty

