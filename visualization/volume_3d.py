"""Interactive 3D brain MRI volume rendering and tumor isosurface extraction."""
from typing import Optional, Dict, Any, Tuple
import numpy as np
import plotly.graph_objects as go
from skimage.transform import resize


def create_3d_volume_figure(
    mri_volume: np.ndarray,
    pred_mask: Optional[np.ndarray] = None,
    scale: float = 0.25,
    show_mri: bool = True,
    show_tumor: bool = True,
    mri_opacity: float = 0.1,
    tumor_opacity: float = 0.85,
    mri_colorscale: str = "Gray",
    tumor_colorscale: str = "Blues",
    title: str = "NeuroTrace — Interactive 3D Brain & Tumor Rendering",
) -> go.Figure:
    """
    Generate an interactive 3D Plotly rendering combining volumetric brain MRI
    and distinct tumor isosurface surfaces.
    
    Args:
        mri_volume: 3D MRI volume array (X, Y, Z).
        pred_mask: Optional 3D binary segmentation mask array (X, Y, Z).
        scale: Downsampling scale factor (e.g. 0.25 for standard fast preview).
        show_mri: Whether to render the semi-transparent brain volume.
        show_tumor: Whether to render the 3D tumor isosurface.
        mri_opacity: Opacity for the brain volume [0.0 - 1.0].
        tumor_opacity: Opacity for the tumor isosurface [0.0 - 1.0].
        mri_colorscale: Colorscale name for the brain volume.
        tumor_colorscale: Colorscale name for the tumor isosurface.
        title: Figure title.
        
    Returns:
        Plotly Figure object for interactive 3D rendering in Streamlit.
    """
    scale = max(0.1, min(scale, 0.5))  # Clamp scale between 0.1 and 0.5 for CPU safety
    target_shape = tuple(max(8, int(s * scale)) for s in mri_volume.shape)

    # 1. Downsample MRI volume for smooth WebGL rendering
    mri_small = resize(
        mri_volume, target_shape, preserve_range=True, anti_aliasing=True
    ).astype(np.float32)

    # Normalize MRI intensity to [0, 255] uint8
    denom = mri_small.max() - mri_small.min() + 1e-6
    mri_norm = ((mri_small - mri_small.min()) / denom * 255.0).astype(np.uint8)

    # Generate 3D spatial grid
    dim_x, dim_y, dim_z = target_shape
    x, y, z = np.mgrid[0:dim_x, 0:dim_y, 0:dim_z]

    fig = go.Figure()

    # 2. Add Brain MRI Volume rendering trace
    if show_mri:
        fig.add_trace(
            go.Volume(
                x=x.flatten(),
                y=y.flatten(),
                z=z.flatten(),
                value=mri_norm.flatten(),
                isomin=int(np.percentile(mri_norm[mri_norm > 0], 10)) if np.any(mri_norm > 0) else 10,
                isomax=255,
                opacity=mri_opacity,
                surface_count=12,
                colorscale=mri_colorscale,
                showscale=False,
                hoverinfo="none",
                name="Brain Volume (FLAIR)",
            )
        )

    # 3. Add Tumor Isosurface trace
    if show_tumor and pred_mask is not None and np.any(pred_mask > 0):
        # Downsample segmentation mask with nearest-neighbor (order=0) to preserve binary values
        pred_small = resize(
            pred_mask.astype(np.float32),
            target_shape,
            order=0,
            preserve_range=True,
            anti_aliasing=False,
        )
        pred_bin = (pred_small > 0.5).astype(np.uint8)

        if np.any(pred_bin > 0):
            fig.add_trace(
                go.Isosurface(
                    x=x.flatten(),
                    y=y.flatten(),
                    z=z.flatten(),
                    value=pred_bin.flatten(),
                    isomin=0.5,
                    isomax=1.0,
                    opacity=tumor_opacity,
                    surface_count=1,
                    colorscale=tumor_colorscale,
                    showscale=False,
                    lighting=dict(
                        ambient=0.45,
                        diffuse=0.8,
                        roughness=0.4,
                        specular=0.5,
                        fresnel=0.2,
                    ),
                    lightposition=dict(x=100, y=100, z=2000),
                    hoverinfo="none",
                    name="Tumor Surface",
                )
            )

    fig.update_layout(
        title=dict(text=title, font=dict(color="#ffffff", size=16)),
        scene=dict(
            xaxis=dict(
                title="Sagittal (X)",
                color="#aaaaaa",
                gridcolor="#333333",
                backgroundcolor="#111111",
                showbackground=True,
            ),
            yaxis=dict(
                title="Coronal (Y)",
                color="#aaaaaa",
                gridcolor="#333333",
                backgroundcolor="#111111",
                showbackground=True,
            ),
            zaxis=dict(
                title="Axial (Z)",
                color="#aaaaaa",
                gridcolor="#333333",
                backgroundcolor="#111111",
                showbackground=True,
            ),
            aspectmode="data",
            camera=dict(
                eye=dict(x=1.6, y=1.6, z=1.3),
                up=dict(x=0, y=0, z=1),
            ),
        ),
        paper_bgcolor="#111111",
        plot_bgcolor="#111111",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            font=dict(color="#ffffff", size=12),
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="#444444",
            borderwidth=1,
        ),
    )

    return fig

