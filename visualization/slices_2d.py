"""Interactive 2D orthogonal multi-planar MRI and segmentation slice viewers."""
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from skimage.measure import find_contours


def normalize_slice_display(img2d: np.ndarray) -> np.ndarray:
    """
    Apply robust 1st-99th percentile contrast normalization for MRI slice display.
    
    Args:
        img2d: 2D numpy array of raw MRI voxel values.
        
    Returns:
        2D float32 array normalized to [0, 1].
    """
    img = img2d.astype(np.float32)
    vmin, vmax = np.percentile(img, [1, 99])
    if vmax > vmin:
        return np.clip((img - vmin) / (vmax - vmin), 0.0, 1.0).astype(np.float32)
    
    # Fallback for flat or low-contrast regions
    denom = img.max() - img.min() + 1e-6
    return ((img - img.min()) / denom).astype(np.float32)


def extract_plane_slice(
    volume: np.ndarray, plane: str, slice_idx: int
) -> np.ndarray:
    """
    Extract a 2D slice along the requested anatomical plane.
    
    Args:
        volume: 3D numpy array of shape (X, Y, Z).
        plane: 'axial' (Z), 'coronal' (Y), or 'sagittal' (X).
        slice_idx: 0-indexed slice coordinate.
        
    Returns:
        2D array oriented for standard radiological display.
    """
    dim_x, dim_y, dim_z = volume.shape
    plane_lower = plane.lower()

    if plane_lower == "axial":
        idx = max(0, min(slice_idx, dim_z - 1))
        # (X, Y) transposed -> horizontal is X (right-left), vertical is Y (posterior-anterior)
        return volume[:, :, idx].T
    elif plane_lower == "coronal":
        idx = max(0, min(slice_idx, dim_y - 1))
        # (X, Z) transposed -> horizontal is X, vertical is Z (inferior-superior)
        return volume[:, idx, :].T
    elif plane_lower == "sagittal":
        idx = max(0, min(slice_idx, dim_x - 1))
        # (Y, Z) transposed -> horizontal is Y, vertical is Z
        return volume[idx, :, :].T
    else:
        raise ValueError(f"Unknown anatomical plane '{plane}'. Must be 'axial', 'coronal', or 'sagittal'.")


def create_orthogonal_slice_figure(
    mri_volume: np.ndarray,
    pred_mask: Optional[np.ndarray] = None,
    plane: str = "axial",
    slice_idx: Optional[int] = None,
    show_mask: bool = True,
    mask_opacity: float = 0.45,
    show_contours: bool = True,
    crosshair: Optional[Tuple[int, int]] = None,
    title: Optional[str] = None,
) -> go.Figure:
    """
    Generate an interactive Plotly 2D slice figure with MRI, segmentation overlay,
    and boundary contours for a given anatomical plane.
    
    Args:
        mri_volume: 3D MRI volume array.
        pred_mask: Optional 3D binary segmentation mask array.
        plane: 'axial', 'coronal', or 'sagittal'.
        slice_idx: Slice index. If None, uses middle slice.
        show_mask: Whether to render the semi-transparent color overlay.
        mask_opacity: Opacity of segmentation overlay [0.0 - 1.0].
        show_contours: Whether to outline tumor boundaries with high-contrast lines.
        crosshair: Optional (col, row) coordinate to display crosshair indicators.
        title: Optional plot title.
        
    Returns:
        Plotly Figure object ready for Streamlit rendering.
    """
    plane_lower = plane.lower()
    dim_x, dim_y, dim_z = mri_volume.shape

    # Default slice index to midpoint
    if slice_idx is None:
        if plane_lower == "axial":
            slice_idx = dim_z // 2
        elif plane_lower == "coronal":
            slice_idx = dim_y // 2
        else:
            slice_idx = dim_x // 2

    # Extract 2D slices
    mri_slice = extract_plane_slice(mri_volume, plane_lower, slice_idx)
    mri_display = normalize_slice_display(mri_slice)
    height, width = mri_display.shape

    mask_slice = None
    if pred_mask is not None:
        mask_slice = extract_plane_slice(pred_mask, plane_lower, slice_idx)

    fig = go.Figure()

    # 1. Base grayscale MRI heatmap
    fig.add_trace(
        go.Heatmap(
            z=mri_display,
            colorscale="Gray",
            showscale=False,
            hoverinfo="none",
            name="FLAIR MRI",
        )
    )

    # 2. Semi-transparent segmentation overlay
    if show_mask and mask_slice is not None and np.any(mask_slice > 0):
        # Create masked array where 0 is transparent (None) and 1 has value
        overlay_z = np.where(mask_slice > 0, 1.0, np.nan)
        fig.add_trace(
            go.Heatmap(
                z=overlay_z,
                colorscale=[[0, "rgba(0,180,255,0)"], [1, f"rgba(0,180,255,{mask_opacity})"]],
                showscale=False,
                hoverinfo="none",
                name="Tumor Mask",
            )
        )

    # 3. High-contrast tumor boundary contours
    if show_contours and mask_slice is not None and np.any(mask_slice > 0):
        contours = find_contours(mask_slice > 0, level=0.5)
        for i, contour in enumerate(contours):
            # contour returns (row, col) coordinates
            c_y = contour[:, 0]
            c_x = contour[:, 1]
            fig.add_trace(
                go.Scatter(
                    x=c_x,
                    y=c_y,
                    mode="lines",
                    line=dict(color="#00ffff", width=2.5),
                    hoverinfo="none",
                    showlegend=(i == 0),
                    name="Tumor Boundary",
                )
            )

    # 4. Optional synchronized crosshairs
    if crosshair is not None:
        cx, cy = crosshair
        fig.add_vline(x=cx, line_width=1, line_dash="dash", line_color="rgba(255,255,0,0.6)")
        fig.add_hline(y=cy, line_width=1, line_dash="dash", line_color="rgba(255,255,0,0.6)")

    # 5. Anatomical orientation annotations
    labels = _get_orientation_labels(plane_lower)
    annotations = [
        dict(x=width / 2, y=-10, text=labels["top"], showarrow=False, font=dict(color="#888", size=11)),
        dict(x=width / 2, y=height + 10, text=labels["bottom"], showarrow=False, font=dict(color="#888", size=11)),
        dict(x=-12, y=height / 2, text=labels["left"], showarrow=False, font=dict(color="#888", size=11)),
        dict(x=width + 12, y=height / 2, text=labels["right"], showarrow=False, font=dict(color="#888", size=11)),
    ]

    title_text = title or f"{plane.title()} View (Slice {slice_idx})"

    fig.update_layout(
        title=dict(text=title_text, font=dict(color="#ffffff", size=14)),
        margin=dict(l=30, r=30, t=40, b=30),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        annotations=annotations,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#fff", size=10),
        ),
    )

    return fig


def create_orthogonal_trio_figure(
    mri_volume: np.ndarray,
    pred_mask: Optional[np.ndarray] = None,
    axial_idx: Optional[int] = None,
    coronal_idx: Optional[int] = None,
    sagittal_idx: Optional[int] = None,
    show_mask: bool = True,
    mask_opacity: float = 0.45,
    show_contours: bool = True,
) -> go.Figure:
    """
    Generate a synchronized 3-panel orthogonal figure (Axial, Coronal, Sagittal) side-by-side.
    """
    dim_x, dim_y, dim_z = mri_volume.shape
    a_idx = axial_idx if axial_idx is not None else dim_z // 2
    c_idx = coronal_idx if coronal_idx is not None else dim_y // 2
    s_idx = sagittal_idx if sagittal_idx is not None else dim_x // 2

    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=[
            f"Axial (Z: {a_idx})",
            f"Coronal (Y: {c_idx})",
            f"Sagittal (X: {s_idx})",
        ],
        horizontal_spacing=0.04,
    )

    planes = [
        ("axial", a_idx, 1),
        ("coronal", c_idx, 2),
        ("sagittal", s_idx, 3),
    ]

    for plane_name, idx, col in planes:
        mri_slice = extract_plane_slice(mri_volume, plane_name, idx)
        mri_disp = normalize_slice_display(mri_slice)

        # Base MRI
        fig.add_trace(
            go.Heatmap(z=mri_disp, colorscale="Gray", showscale=False, hoverinfo="none"),
            row=1,
            col=col,
        )

        # Mask overlay
        if show_mask and pred_mask is not None:
            mask_slice = extract_plane_slice(pred_mask, plane_name, idx)
            if np.any(mask_slice > 0):
                overlay = np.where(mask_slice > 0, 1.0, np.nan)
                fig.add_trace(
                    go.Heatmap(
                        z=overlay,
                        colorscale=[[0, "rgba(0,180,255,0)"], [1, f"rgba(0,180,255,{mask_opacity})"]],
                        showscale=False,
                        hoverinfo="none",
                    ),
                    row=1,
                    col=col,
                )

                # Contours
                if show_contours:
                    contours = find_contours(mask_slice > 0, level=0.5)
                    for contour in contours:
                        fig.add_trace(
                            go.Scatter(
                                x=contour[:, 1],
                                y=contour[:, 0],
                                mode="lines",
                                line=dict(color="#00ffff", width=2),
                                hoverinfo="none",
                                showlegend=False,
                            ),
                            row=1,
                            col=col,
                        )

    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        showlegend=False,
        font=dict(color="#ffffff"),
    )

    for i in range(1, 4):
        fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=i)
        fig.update_yaxes(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor=f"x{i}" if i > 1 else "x",
            scaleratio=1,
            row=1,
            col=i,
        )

    return fig


def _get_orientation_labels(plane: str) -> Dict[str, str]:
    """Return standard anatomical direction labels for a plane."""
    if plane == "axial":
        return {"top": "Anterior (A)", "bottom": "Posterior (P)", "left": "Right (R)", "right": "Left (L)"}
    elif plane == "coronal":
        return {"top": "Superior (S)", "bottom": "Inferior (I)", "left": "Right (R)", "right": "Left (L)"}
    else:  # sagittal
        return {"top": "Superior (S)", "bottom": "Inferior (I)", "left": "Anterior (A)", "right": "Posterior (P)"}

