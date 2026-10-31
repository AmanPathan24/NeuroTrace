"""
NeuroTrace — Agentic Brain MRI Segmentation Analysis & Research Copilot.
Editorial Research Instrument: Serif display, Plex UI, hairlines, and evidence grounding.
Refactored with the NeuroTrace design system matching ui_reference.
"""
import io
import os
import glob
import gzip
import json
import inspect
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import numpy as np
import nibabel as nib
import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="NeuroTrace — Brain MRI Research Copilot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Forward and backward compatible stretch width kwargs for Streamlit
HAS_WIDTH_ARG = "width" in inspect.signature(st.button).parameters
STRETCH_KW = {"width": "stretch"} if HAS_WIDTH_ARG else {"use_container_width": True}

# Inject NeuroTrace Editorial Research Design System CSS
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,300;8..60,400;8..60,500;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
    :root {
        --font-ui: 'IBM Plex Sans', -apple-system, sans-serif;
        --font-display: 'Source Serif 4', Georgia, serif;
        --font-mono: 'IBM Plex Mono', monospace;
        --paper: #0C1011;
        --panel: #131819;
        --sunken: #0F1415;
        --line: #232A2A;
        --line-2: #2F3737;
        --accent: #6FB2A9;
        --accent-soft: #172B2A;
        --accent-ink: #9FD3CB;
        --ink: #E9EDEB;
        --ink-2: #A6B0AF;
        --ink-3: #778281;
        --ink-4: #596363;
        --ok: #7CB494;
        --warn: #D2AE6B;
        --danger: #DC9288;
        --viewer: #070A0B;
    }

    /* Base Streamlit App Overrides */
    .stApp {
        background-color: var(--paper) !important;
        color: var(--ink) !important;
        font-family: var(--font-ui) !important;
    }

    [data-testid="stSidebar"] {
        background-color: var(--sunken) !important;
        border-right: 1px solid var(--line) !important;
    }

    /* Brand Header */
    .brand-title {
        font-family: var(--font-display) !important;
        font-size: 1.85rem !important;
        font-weight: 500 !important;
        color: var(--ink) !important;
        line-height: 1.15;
        letter-spacing: -0.015em;
    }

    .eyebrow {
        font-family: var(--font-mono) !important;
        font-size: 0.68rem !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        color: var(--ink-3) !important;
        font-weight: 500 !important;
    }

    .mono {
        font-family: var(--font-mono) !important;
    }

    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        height: 22px;
        padding: 0 8px;
        border-radius: 3px;
        font-size: 11px;
        font-weight: 500;
        white-space: nowrap;
    }
    .badge-ok {
        color: var(--ok);
        background: rgba(124, 180, 148, 0.12);
        border: 1px solid rgba(124, 180, 148, 0.28);
    }
    .badge-accent {
        color: var(--accent-ink);
        background: var(--accent-soft);
        border: 1px solid rgba(111, 178, 169, 0.35);
    }
    .badge-warn {
        color: var(--warn);
        background: rgba(210, 174, 107, 0.12);
        border: 1px solid rgba(210, 174, 107, 0.28);
    }
    .badge-danger {
        color: var(--danger);
        background: rgba(220, 146, 136, 0.12);
        border: 1px solid rgba(220, 146, 136, 0.28);
    }
    .badge-line {
        color: var(--ink-3);
        background: transparent;
        border: 1px solid var(--line-2);
    }
    .chip-mono {
        font-family: var(--font-mono) !important;
        font-size: 10.5px !important;
    }

    /* StatCells Row from ui_reference */
    .stat-card-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        margin-bottom: 20px;
        overflow: hidden;
    }
    .stat-cell {
        padding: 16px 18px;
        border-left: 1px solid var(--line);
    }
    .stat-cell:first-child {
        border-left: none;
    }
    .stat-label {
        font-family: var(--font-mono);
        font-size: 10px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--ink-3);
    }
    .stat-val {
        font-family: var(--font-display);
        font-size: 26px;
        line-height: 1.15;
        margin-top: 6px;
        color: var(--ink);
        letter-spacing: -0.02em;
    }
    .stat-unit {
        font-family: var(--font-ui);
        font-size: 12px;
        color: var(--ink-3);
        margin-left: 4px;
    }
    .stat-meta {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 6px;
        font-size: 11.5px;
        color: var(--ink-3);
    }

    /* Card container */
    .nt-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 16px 18px;
        margin-bottom: 16px;
    }
    .nt-card-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid var(--line);
        padding-bottom: 10px;
        margin-bottom: 14px;
    }
    .nt-card-title {
        font-family: var(--font-display);
        font-size: 1.15rem;
        font-weight: 500;
        color: var(--ink);
    }

    /* Tool call indicator */
    .tool-call {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid var(--line);
        background: var(--sunken);
        border-radius: 4px;
        padding: 6px 10px;
        margin-bottom: 8px;
        font-family: var(--font-mono);
        font-size: 11px;
        color: var(--ink-2);
    }

    /* Research Notice */
    .research-notice {
        background-color: rgba(23, 43, 42, 0.45);
        border-left: 3px solid var(--accent);
        border-radius: 4px;
        padding: 9px 13px;
        font-size: 0.82rem;
        color: var(--ink-2);
        margin-bottom: 18px;
    }

    /* Viewer header bar */
    .viewer-header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--viewer);
        border: 1px solid var(--line);
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        padding: 8px 14px;
        font-family: var(--font-mono);
        font-size: 11px;
        color: var(--ink-3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

from config.settings import get_settings
from imaging.loader import NiftiLoader, load_and_validate_mri
from models.adapter import NeuroSegNetAdapter
from models.exporter import export_segmentation_nifti
from analysis.measurements import calculate_tumor_measurements
from analysis.qc import inspect_segmentation_quality
from visualization.slices_2d import (
    create_orthogonal_slice_figure,
    create_orthogonal_trio_figure,
)
from visualization.volume_3d import create_3d_volume_figure
from agents.copilot import get_research_copilot, GemmaResearchCopilot
from agents.tools import ResearchToolRegistry
from reporting.pdf_generator import generate_research_pdf_report


@st.cache_resource(show_spinner=False)
def get_cached_adapter() -> NeuroSegNetAdapter:
    """Load and cache the verified 3D U-Net adapter."""
    return NeuroSegNetAdapter()


@st.cache_resource(show_spinner=False)
def get_cached_copilot() -> GemmaResearchCopilot:
    """Load and cache the Gemma research copilot."""
    return get_research_copilot()


def init_session_state():
    """Initialize persistent Streamlit session variables."""
    if "study" not in st.session_state:
        st.session_state.study = None
    if "raw_volume" not in st.session_state:
        st.session_state.raw_volume = None
    if "nii_img" not in st.session_state:
        st.session_state.nii_img = None
    if "pred_mask" not in st.session_state:
        st.session_state.pred_mask = None
    if "pred_meta" not in st.session_state:
        st.session_state.pred_meta = None
    if "metrics" not in st.session_state:
        st.session_state.metrics = None
    if "qc" not in st.session_state:
        st.session_state.qc = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


init_session_state()
settings = get_settings()
adapter = get_cached_adapter()
copilot = get_cached_copilot()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    # Sidebar Header with concentric brandmark
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
            <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="#6FB2A9">
                <circle cx="12" cy="12" r="9" stroke-width="1.2" opacity=".38" />
                <circle cx="12" cy="12" r="5.4" stroke-width="1.5" />
                <path d="M12 2.6v4.4M12 17v4.4M2.6 12h4.4M17 12h4.4" stroke-width="1.2" opacity=".55" />
                <circle cx="12" cy="12" r="1.3" fill="#6FB2A9" stroke="none" />
            </svg>
            <div>
                <div style="font-family: var(--font-display); font-size: 1.15rem; font-weight: 500; color: #E9EDEB;">NeuroTrace</div>
                <div class="eyebrow" style="font-size: 9px;">Neuroimaging Lab</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown('<div class="eyebrow">1. Ingest Brain MRI Scan</div>', unsafe_allow_html=True)
    input_source = st.radio("Source Format:", ["Sample BraTS Volume", "Upload NIfTI (.nii/.nii.gz)"])

    selected_file_path = None
    uploaded_file = None

    if input_source == "Sample BraTS Volume":
        sample_scans = sorted(glob.glob("BRATS/*.nii"))
        if sample_scans:
            scan_options = {Path(p).name: p for p in sample_scans}
            chosen_name = st.selectbox("Benchmark Scan:", list(scan_options.keys()))
            selected_file_path = scan_options[chosen_name]
        else:
            st.warning("No sample scans found in BRATS/ directory.")
    else:
        uploaded_file = st.file_uploader(
            "Upload Brain MRI Scan", type=["nii", "gz"], help="Supports .nii and .nii.gz NIfTI formats"
        )

    load_btn = st.button("📥 Load & Validate MRI", **STRETCH_KW)

    if load_btn:
        try:
            with st.spinner("Validating NIfTI geometry..."):
                if input_source == "Sample BraTS Volume" and selected_file_path:
                    raw_data, nii_img, study = NiftiLoader.load_from_path(selected_file_path)
                elif uploaded_file:
                    file_bytes = uploaded_file.read()
                    raw_data, nii_img, study = NiftiLoader.load_from_bytes(
                        file_bytes=file_bytes, filename=uploaded_file.name
                    )
                else:
                    st.error("Please select or upload a valid MRI scan.")
                    st.stop()

                # Update session
                st.session_state.study = study
                st.session_state.raw_volume = raw_data
                st.session_state.nii_img = nii_img
                st.session_state.pred_mask = None
                st.session_state.pred_meta = None
                st.session_state.metrics = None
                st.session_state.qc = None
                st.session_state.chat_history = []

                # Register in agent registry
                copilot.registry.register_study_session(study=study, raw_volume=raw_data)
                st.success(f"Study `{study.metadata.study_id}` loaded & validated!")
        except Exception as e:
            st.error(f"Ingestion failed: {e}")

    st.divider()
    st.markdown('<div class="eyebrow">2. Model & Execution Engine</div>', unsafe_allow_html=True)
    model_info = adapter.get_model_info()
    st.markdown(
        f"""
        <div style="font-size: 0.8rem; color: #A6B0AF; line-height: 1.6; margin-top: 4px;">
            <div>• <b>Architecture</b>: <span class="mono">3D U-Net (8 filters)</span></div>
            <div>• <b>Parameters</b>: <span class="mono">{model_info['total_parameters']:,}</span></div>
            <div>• <b>Checkpoint</b>: <span class="mono">Epoch 45</span></div>
            <div>• <b>Device</b>: <span class="mono">{model_info['device'].upper()}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.study is not None:
        seg_btn = st.button("🚀 Run NeuroSegNet Segmentation", type="primary", **STRETCH_KW)
        if seg_btn:
            try:
                with st.spinner("Executing 3D U-Net inference on CPU..."):
                    pred_mask, pred_meta = adapter.predict(
                        st.session_state.raw_volume,
                        study_id=st.session_state.study.metadata.study_id,
                    )
                    metrics = calculate_tumor_measurements(
                        pred_mask=pred_mask,
                        raw_volume=st.session_state.raw_volume,
                        voxel_spacing=st.session_state.study.spacing,
                        affine=np.array(st.session_state.study.affine_matrix),
                        study_id=st.session_state.study.metadata.study_id,
                        prediction_id=pred_meta.prediction_id,
                    )
                    qc = inspect_segmentation_quality(
                        pred_mask=pred_mask,
                        raw_volume=st.session_state.raw_volume,
                        study_id=st.session_state.study.metadata.study_id,
                        prediction_id=pred_meta.prediction_id,
                    )

                    st.session_state.pred_mask = pred_mask
                    st.session_state.pred_meta = pred_meta
                    st.session_state.metrics = metrics
                    st.session_state.qc = qc

                    copilot.registry.register_study_session(
                        study=st.session_state.study,
                        raw_volume=st.session_state.raw_volume,
                        pred_mask=pred_mask,
                        metrics=metrics,
                        qc=qc,
                    )
                st.success(f"Inference complete in {pred_meta.inference_seconds:.2f}s!")
            except Exception as e:
                st.error(f"Segmentation failed: {e}")

    st.divider()
    st.markdown('<div class="eyebrow">3. Gemma 4 Copilot Config</div>', unsafe_allow_html=True)
    selected_gemma = st.selectbox(
        "Gemma 4 Model:",
        ["gemma-4-31b-it", "gemma-4-26b-a4b-it"],
        index=0 if settings.gemma_model_id == "gemma-4-31b-it" else 1,
        help="Supported models:\n• gemma-4-31b-it (31B Dense)\n• gemma-4-26b-a4b-it (26B MoE with 4B active)",
    )
    copilot.set_model(selected_gemma)

    api_key_input = st.text_input(
        "Gemini API Key (Optional):",
        value=settings.gemini_api_key or "",
        type="password",
        help="Optional API key for live Google GenAI queries. If omitted, uses local deterministic grounding.",
    )
    if api_key_input != (copilot.api_key or ""):
        copilot.set_api_key(api_key_input)

    status = copilot.get_copilot_status()
    if status["is_online"]:
        st.markdown(f'<span class="badge badge-ok chip-mono">🟢 Gemma 4 Online ({selected_gemma})</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge badge-accent chip-mono">🟡 Local Grounding ({selected_gemma})</span>', unsafe_allow_html=True)

    st.divider()
    st.caption("NeuroTrace v1.0 • Editorial Research Platform")

# ----------------- MAIN WORKSPACE -----------------
active_study_label = st.session_state.study.metadata.study_id if st.session_state.study else "NO SCAN LOADED"
status_tone = "badge-ok" if st.session_state.pred_mask is not None else ("badge-accent" if st.session_state.study else "badge-line")
status_text = "Analysis Complete" if st.session_state.pred_mask is not None else ("Scan Validated" if st.session_state.study else "Awaiting Input")

st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--line);">
        <div style="display: flex; align-items: center; gap: 12px;">
            <svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="#6FB2A9">
                <circle cx="12" cy="12" r="9" stroke-width="1.2" opacity=".38" />
                <circle cx="12" cy="12" r="5.4" stroke-width="1.5" />
                <path d="M12 2.6v4.4M12 17v4.4M2.6 12h4.4M17 12h4.4" stroke-width="1.2" opacity=".55" />
                <circle cx="12" cy="12" r="1.3" fill="#6FB2A9" stroke="none" />
            </svg>
            <div>
                <div class="brand-title">NeuroTrace</div>
                <div class="eyebrow" style="margin-top: 2px;">Editorial Research Instrument · From Segmentation to Evidence</div>
            </div>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
            <span class="badge badge-line chip-mono">{active_study_label}</span>
            <span class="badge {status_tone} chip-mono">● {status_text}</span>
            <span class="badge badge-accent chip-mono">{copilot.model_name}</span>
        </div>
    </div>
    <div class="research-notice">
        <b>Academic Research Notice</b>: NeuroTrace is an educational and computational neuroimaging research system. 
        Not for clinical diagnosis, prognosis, or surgical treatment planning.
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.study is None:
    st.info("👈 Select a sample BraTS benchmark volume or upload a NIfTI scan in the sidebar to begin analysis.")
    st.stop()

study = st.session_state.study
raw_vol = st.session_state.raw_volume
pred_mask = st.session_state.pred_mask
metrics = st.session_state.metrics
qc = st.session_state.qc

# Top StatCells Row from ui_reference when segmentation is complete
if metrics is not None and qc is not None:
    st.markdown(
        f"""
        <div class="stat-card-row">
            <div class="stat-cell">
                <div class="stat-label">Whole Tumor Volume</div>
                <div class="stat-val">{metrics.physical_volume_cm3:.2f}<span class="stat-unit">mL</span></div>
                <div class="stat-meta"><span style="color: var(--accent); font-weight: 500;">{metrics.tumor_volume_fraction_percent:.2f}%</span><span>of brain tissue</span></div>
            </div>
            <div class="stat-cell">
                <div class="stat-label">Segmented Voxels</div>
                <div class="stat-val">{metrics.tumor_voxel_count:,}</div>
                <div class="stat-meta"><span class="mono">Spacing {study.spacing.dx_mm:.1f}×{study.spacing.dy_mm:.1f}×{study.spacing.dz_mm:.1f} mm</span></div>
            </div>
            <div class="stat-cell">
                <div class="stat-label">QC Plausibility Gate</div>
                <div class="stat-val" style="color: {'var(--ok)' if qc.is_passed else 'var(--warn)'};">{'PASSED' if qc.is_passed else 'FLAGGED'}</div>
                <div class="stat-meta"><span>SNR {qc.signal_to_noise_ratio_est:.2f} · Contrast {qc.contrast_ratio_est:.2f}</span></div>
            </div>
            <div class="stat-cell">
                <div class="stat-label">Inference Runtime</div>
                <div class="stat-val">{st.session_state.pred_meta.inference_seconds:.2f}<span class="stat-unit">s</span></div>
                <div class="stat-meta"><span>nt-seg 3D U-Net · CPU</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------- WORKSPACE TABS -----------------
tabs = st.tabs([
    "Overview & Lab Workspace",
    "Orthogonal 2D Viewer",
    "Interactive 3D Volume",
    "Quantitative Volumetrics",
    "Quality Control & Flags",
    "Gemma 4 Copilot",
    "Research Report & Export",
])

# ----- TAB 1: Overview & Lab Workspace -----
with tabs[0]:
    st.markdown("### Overview & Ingestion Metadata")
    col_ov1, col_ov2 = st.columns(2)

    with col_ov1:
        st.markdown(
            f"""
            <div class="nt-card">
                <div class="nt-card-head">
                    <span class="nt-card-title">Study & Geometry Specifications</span>
                    <span class="badge badge-accent chip-mono">NIfTI-1</span>
                </div>
                <div style="font-size: 0.85rem; line-height: 1.8; color: #A6B0AF;">
                    <div>• <b>Study Identifier</b>: <span class="mono" style="color: #E9EDEB;">{study.metadata.study_id}</span></div>
                    <div>• <b>Original Filename</b>: <span class="mono" style="color: #E9EDEB;">{study.metadata.filename}</span></div>
                    <div>• <b>Modality</b>: <span class="mono" style="color: #E9EDEB;">{study.metadata.modality}</span></div>
                    <div>• <b>Spatial Matrix</b>: <span class="mono" style="color: #E9EDEB;">{study.dimensions.dim_x} × {study.dimensions.dim_y} × {study.dimensions.dim_z}</span></div>
                    <div>• <b>Voxel Dimensions</b>: <span class="mono" style="color: #E9EDEB;">{study.spacing.dx_mm:.2f} × {study.spacing.dy_mm:.2f} × {study.spacing.dz_mm:.2f} mm</span></div>
                    <div>• <b>Voxel Unit Volume</b>: <span class="mono" style="color: #E9EDEB;">{study.spacing.voxel_volume_mm3:.3f} mm³</span></div>
                    <div>• <b>Orientation</b>: <span class="mono" style="color: #E9EDEB;">{study.orientation}</span></div>
                    <div>• <b>SHA-256 Provenance</b>: <span class="mono" style="font-size: 10px;">{study.metadata.sha256_hash[:32]}...</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_ov2:
        st.markdown(
            f"""
            <div class="nt-card">
                <div class="nt-card-head">
                    <span class="nt-card-title">Intensity Distribution & Normalization</span>
                    <span class="badge badge-ok chip-mono">Verified</span>
                </div>
                <div style="font-size: 0.85rem; line-height: 1.8; color: #A6B0AF;">
                    <div>• <b>Minimum Intensity</b>: <span class="mono" style="color: #E9EDEB;">{study.intensity_stats.min_value:.2f}</span></div>
                    <div>• <b>Maximum Intensity</b>: <span class="mono" style="color: #E9EDEB;">{study.intensity_stats.max_value:.2f}</span></div>
                    <div>• <b>Mean Parenchymal Value</b>: <span class="mono" style="color: #E9EDEB;">{study.intensity_stats.mean_value:.2f}</span></div>
                    <div>• <b>Standard Deviation</b>: <span class="mono" style="color: #E9EDEB;">{study.intensity_stats.std_value:.2f}</span></div>
                    <div>• <b>1st Percentile ($P_1$)</b>: <span class="mono" style="color: #E9EDEB;">{study.intensity_stats.p01_value:.2f}</span></div>
                    <div>• <b>99th Percentile ($P_{{99}}$)</b>: <span class="mono" style="color: #E9EDEB;">{study.intensity_stats.p99_value:.2f}</span></div>
                    <div>• <b>Preprocessing Standard</b>: <span class="mono" style="color: #E9EDEB;">Z-score Zero-Mean Unit-Variance</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="nt-card-title" style="margin-top: 10px; margin-bottom: 8px;">Scanner World Coordinate Affine Matrix (4×4)</div>', unsafe_allow_html=True)
    st.dataframe(np.array(study.affine_matrix), **STRETCH_KW)

# ----- TAB 2: Orthogonal 2D Viewer -----
with tabs[1]:
    st.markdown(
        """
        <div class="viewer-header-bar">
            <span>ORTHOGONAL 2D MULTI-PLANAR VIEWER</span>
            <span>AXIAL · CORONAL · SAGITTAL · RADIOLOGICAL ORIENTATION</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_vctrl1, col_vctrl2, col_vctrl3 = st.columns(3)
    with col_vctrl1:
        show_mask_2d = st.checkbox("Overlay Segmentation Mask", value=True)
    with col_vctrl2:
        show_contours_2d = st.checkbox("Draw Boundary Contours", value=True)
    with col_vctrl3:
        mask_opacity = st.slider("Overlay Opacity", 0.1, 1.0, 0.45, 0.05)

    view_mode = st.radio("Display Mode:", ["Synchronized Trio (Axial, Coronal, Sagittal)", "Diagnostic Plane Explorer"], horizontal=True)

    if view_mode.startswith("Synchronized"):
        fig_trio = create_orthogonal_trio_figure(
            mri_volume=raw_vol,
            pred_mask=pred_mask,
            show_mask=show_mask_2d,
            mask_opacity=mask_opacity,
            show_contours=show_contours_2d,
        )
        st.plotly_chart(fig_trio, use_container_width=True)
    else:
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            chosen_plane = st.selectbox("Anatomical Plane:", ["axial", "coronal", "sagittal"])
            dim_limit = {"axial": raw_vol.shape[2], "coronal": raw_vol.shape[1], "sagittal": raw_vol.shape[0]}[chosen_plane]

            default_idx = dim_limit // 2
            if metrics and metrics.centroid_voxel:
                if chosen_plane == "axial":
                    default_idx = int(metrics.centroid_voxel[2])
                elif chosen_plane == "coronal":
                    default_idx = int(metrics.centroid_voxel[1])
                else:
                    default_idx = int(metrics.centroid_voxel[0])

            slice_idx = st.slider(f"{chosen_plane.title()} Slice Index", 0, dim_limit - 1, default_idx)

        with col_p2:
            fig_single = create_orthogonal_slice_figure(
                mri_volume=raw_vol,
                pred_mask=pred_mask,
                plane=chosen_plane,
                slice_idx=slice_idx,
                show_mask=show_mask_2d,
                mask_opacity=mask_opacity,
                show_contours=show_contours_2d,
            )
            st.plotly_chart(fig_single, use_container_width=True)

# ----- TAB 3: Interactive 3D Volume -----
with tabs[2]:
    st.markdown(
        """
        <div class="viewer-header-bar">
            <span>INTERACTIVE 3D ISOSURFACE & VOLUME RENDERING</span>
            <span>6-DOF ROTATE · PAN · ZOOM · WEBGL ACCELERATED</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c3d_1, c3d_2, c3d_3, c3d_4 = st.columns(4)
    with c3d_1:
        show_mri_3d = st.checkbox("Render Brain Volume", value=True)
    with c3d_2:
        show_tumor_3d = st.checkbox("Render Tumor Isosurface", value=True)
    with c3d_3:
        mri_opacity_3d = st.slider("Brain Opacity", 0.05, 0.40, 0.10, 0.05)
    with c3d_4:
        scale_3d = st.select_slider("Resolution Scale", options=[0.15, 0.20, 0.25, 0.35], value=0.25)

    if pred_mask is None:
        st.info("Run segmentation in the sidebar to render the 3D tumor lesion isosurface.")

    fig_3d = create_3d_volume_figure(
        mri_volume=raw_vol,
        pred_mask=pred_mask,
        scale=scale_3d,
        show_mri=show_mri_3d,
        show_tumor=show_tumor_3d,
        mri_opacity=mri_opacity_3d,
        tumor_opacity=0.85,
    )
    st.plotly_chart(fig_3d, use_container_width=True)

# ----- TAB 4: Quantitative Volumetrics -----
with tabs[3]:
    st.markdown("### Quantitative Volumetric Measurements & Spatial Distribution")
    if metrics is None:
        st.info("Execute segmentation to compute deterministic volumetric measurements.")
    else:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(
                f"""
                <div class="nt-card">
                    <div class="nt-card-head">
                        <span class="nt-card-title">Volumetric & Extent Metrics</span>
                        <span class="badge badge-accent chip-mono">Deterministic</span>
                    </div>
                    <div style="font-size: 0.85rem; line-height: 1.8; color: #A6B0AF;">
                        <div>• <b>Physical Tumor Volume</b>: <span class="mono" style="color: #6FB2A9; font-weight: 600;">{metrics.physical_volume_cm3:.3f} mL (cm³)</span></div>
                        <div>• <b>Total Tumor Voxels</b>: <span class="mono" style="color: #E9EDEB;">{metrics.tumor_voxel_count:,} voxels</span></div>
                        <div>• <b>Total Non-Zero Brain Tissue</b>: <span class="mono" style="color: #E9EDEB;">{metrics.total_brain_voxels:,} voxels</span></div>
                        <div>• <b>Parenchymal Involvement</b>: <span class="mono" style="color: #E9EDEB;">{metrics.tumor_volume_fraction_percent:.3f}%</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if metrics.bounding_box:
                bb = metrics.bounding_box
                st.markdown(
                    f"""
                    <div class="nt-card">
                        <div class="nt-card-head">
                            <span class="nt-card-title">3D Bounding Box Geometry</span>
                            <span class="badge badge-line chip-mono">Aligned</span>
                        </div>
                        <div style="font-size: 0.85rem; line-height: 1.8; color: #A6B0AF;">
                            <div>• <b>Sagittal (X) Range</b>: <span class="mono">[{bb.x_min}, {bb.x_max}]</span></div>
                            <div>• <b>Coronal (Y) Range</b>: <span class="mono">[{bb.y_min}, {bb.y_max}]</span></div>
                            <div>• <b>Axial (Z) Range</b>: <span class="mono">[{bb.z_min}, {bb.z_max}]</span></div>
                            <div>• <b>Bounding Extents</b>: <span class="mono">{bb.dimensions[0]} × {bb.dimensions[1]} × {bb.dimensions[2]} voxels</span></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_m2:
            if metrics.centroid_voxel and metrics.centroid_world_mm:
                st.markdown(
                    f"""
                    <div class="nt-card">
                        <div class="nt-card-head">
                            <span class="nt-card-title">Spatial Centroid Coordinates</span>
                            <span class="badge badge-ok chip-mono">Verified</span>
                        </div>
                        <div style="font-size: 0.85rem; line-height: 1.8; color: #A6B0AF;">
                            <div>• <b>Voxel Index Space</b>: <span class="mono" style="color: #E9EDEB;">({metrics.centroid_voxel[0]}, {metrics.centroid_voxel[1]}, {metrics.centroid_voxel[2]})</span></div>
                            <div>• <b>Scanner Millimeter Space</b>: <span class="mono" style="color: #6FB2A9;">({metrics.centroid_world_mm[0]:.2f}, {metrics.centroid_world_mm[1]:.2f}, {metrics.centroid_world_mm[2]:.2f}) mm</span></div>
                            <div>• <b>Ground Truth Accuracy</b>: <span style="color: #D2AE6B;">Unavailable (No Reference Mask Provided)</span></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if metrics.slice_distribution:
            st.markdown('<div class="nt-card-title" style="margin-top: 14px; margin-bottom: 8px;">Diagnostic Slices with Highest Tumor Load</div>', unsafe_allow_html=True)
            dist_cols = st.columns(3)
            for i, plane in enumerate(["axial", "coronal", "sagittal"]):
                with dist_cols[i]:
                    st.markdown(f'<div class="eyebrow">{plane.upper()} PLANE</div>', unsafe_allow_html=True)
                    records = metrics.slice_distribution.get(plane, [])
                    if records:
                        table_html = "<table style='width: 100%; font-size: 11.5px; border-collapse: collapse; margin-top: 6px;'>"
                        table_html += "<tr style='border-bottom: 1px solid #232A2A; color: #778281;'><th style='text-align:left; padding:4px;'>Slice</th><th style='text-align:right; padding:4px;'>Voxels</th><th style='text-align:right; padding:4px;'>Area (cm²)</th></tr>"
                        for r in records[:5]:
                            table_html += f"<tr style='border-bottom: 1px solid #1a2223;'><td style='padding:4px;' class='mono'>{r['slice_idx']}</td><td style='text-align:right; padding:4px;' class='mono'>{r['tumor_voxels']:,}</td><td style='text-align:right; padding:4px;' class='mono'>{r['tumor_area_cm2']:.2f}</td></tr>"
                        table_html += "</table>"
                        st.markdown(table_html, unsafe_allow_html=True)

# ----- TAB 5: Quality Control & Flags -----
with tabs[4]:
    st.markdown("### Technical Quality Control Gate & Artifact Checks")
    if qc is None:
        st.info("Execute segmentation to compute technical quality control evaluations.")
    else:
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            status_cls = "badge-ok" if qc.is_passed else "badge-warn"
            st.markdown(
                f"""
                <div class="nt-card">
                    <div class="nt-card-head">
                        <span class="nt-card-title">Automated Technical Gate</span>
                        <span class="badge {status_cls} chip-mono">{'PASSED' if qc.is_passed else 'FLAGGED'}</span>
                    </div>
                    <div style="font-size: 0.85rem; line-height: 1.8; color: #A6B0AF;">
                        <div>• <b>Signal-to-Noise Ratio (SNR)</b>: <span class="mono" style="color: #E9EDEB;">{qc.signal_to_noise_ratio_est:.2f}</span></div>
                        <div>• <b>Tumor-to-Brain Contrast</b>: <span class="mono" style="color: #E9EDEB;">{qc.contrast_ratio_est:.2f}</span></div>
                        <div>• <b>Brain Fraction of Matrix</b>: <span class="mono" style="color: #E9EDEB;">{qc.brain_voxel_fraction * 100:.1f}%</span></div>
                        <div>• <b>Finding Type</b>: <span class="mono" style="color: #E9EDEB;">{'Negative (No Lesion Segmented)' if qc.is_empty_mask else 'Positive (Tumor Lesion Segmented)'}</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with q_col2:
            st.markdown(
                """
                <div class="nt-card">
                    <div class="nt-card-head">
                        <span class="nt-card-title">Quality Gate Observations & Flags</span>
                        <span class="badge badge-line chip-mono">Integrity</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            if qc.flags:
                for flag in qc.flags:
                    st.warning(f"• {flag}")
            else:
                st.success("• No anomalous boundary leakage, false positives in air, or fragmentation detected.")
            st.markdown("</div>", unsafe_allow_html=True)

# ----- TAB 6: Gemma 4 Copilot -----
with tabs[5]:
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
            <div style="font-family: var(--font-display); font-size: 1.3rem; font-weight: 500; color: #E9EDEB;">Google Gemma 4 Research Copilot</div>
            <span class="badge badge-accent chip-mono">{copilot.model_name}</span>
        </div>
        <div class="tool-call">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="#6FB2A9" stroke-width="2"><path d="M3.6 5.2h16.8v13.6H3.6z"/><path d="M7.2 9.4 9.6 11.8 7.2 14.2M12.4 14.4h4"/></svg>
            <span style="color: #E9EDEB;">neurosegnet_tool_registry</span>
            <span style="opacity: .6;">(calculate_tumor_volumes, inspect_segmentation_quality, validate_mri_study)</span>
            <span style="color: var(--ok); font-weight: 500; margin-left: 6px;">✓ Evidence Grounded</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    quick_prompts = [
        "Summarize the volumetric findings and bounding box",
        "Explain the technical quality control observations",
        "Which slices have the highest tumor involvement?",
    ]
    qp_cols = st.columns(3)
    selected_prompt = None
    for i, qp in enumerate(quick_prompts):
        with qp_cols[i]:
            if st.button(qp, key=f"qp_{i}", **STRETCH_KW):
                selected_prompt = qp

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask Gemma 4 about this MRI analysis...") or selected_prompt

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing verified evidence with Gemma 4..."):
                reply = copilot.chat(user_input, study_id=study.metadata.study_id)
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ----- TAB 7: Research Report & Export -----
with tabs[6]:
    st.markdown("### Reproducible Research Report & Export")
    if metrics is None or qc is None:
        st.info("Run segmentation analysis in the sidebar to enable report generation and exports.")
    else:
        col_rep1, col_rep2 = st.columns(2)
        with col_rep1:
            st.markdown(
                f"""
                <div class="nt-card">
                    <div class="nt-card-head">
                        <span class="nt-card-title">📄 Publication-Grade PDF Report</span>
                        <span class="badge badge-accent chip-mono">ReportLab</span>
                    </div>
                    <p style="font-size: 0.85rem; color: #A6B0AF; line-height: 1.6;">
                        Generates a publication-grade, multi-page PDF document incorporating study metadata, 
                        3D U-Net provenance, deterministic measurements, QC checks, embedded orthogonal slice thumbnails, 
                        and AI research commentary attributed to <b>{copilot.model_name}</b>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Generate PDF Research Report", type="primary", **STRETCH_KW):
                with st.spinner("Compiling PDF report and embedding high-res figures..."):
                    pdf_path = generate_research_pdf_report(
                        study=study,
                        metrics=metrics,
                        qc=qc,
                        prediction_metadata=st.session_state.pred_meta,
                        ai_commentary=copilot.synthesize_research_summary(study.metadata.study_id),
                        raw_volume=raw_vol,
                        pred_mask=pred_mask,
                        copilot_model=copilot.model_name,
                    )
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="⬇️ Download PDF Research Report",
                        data=pdf_bytes,
                        file_name=f"neurotrace_report_{study.metadata.study_id}.pdf",
                        mime="application/pdf",
                        **STRETCH_KW,
                    )
                    st.success("PDF Report compiled successfully!")

        with col_rep2:
            st.markdown(
                """
                <div class="nt-card">
                    <div class="nt-card-head">
                        <span class="nt-card-title">📦 NIfTI Mask & JSON Bundle</span>
                        <span class="badge badge-ok chip-mono">In-Memory</span>
                    </div>
                    <p style="font-size: 0.85rem; color: #A6B0AF; line-height: 1.6;">
                        Export the binary segmentation mask as a compressed NIfTI file (<span class="mono">.nii.gz</span>) 
                        preserving original affine geometry, alongside the complete JSON reproducibility record.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Build in-memory compressed NIfTI segmentation mask
            new_header = st.session_state.nii_img.header.copy()
            new_header.set_data_dtype(np.uint8)
            seg_nii = nib.Nifti1Image(
                dataobj=pred_mask.astype(np.uint8),
                affine=st.session_state.nii_img.affine,
                header=new_header,
            )
            raw_nii_bytes = seg_nii.to_bytes()
            compressed_nii_bytes = gzip.compress(raw_nii_bytes)

            st.download_button(
                label="⬇️ Download Segmentation Mask (.nii.gz)",
                data=compressed_nii_bytes,
                file_name=f"segmentation_{study.metadata.study_id}.nii.gz",
                mime="application/gzip",
                **STRETCH_KW,
            )

            # JSON Bundle
            json_bundle = {
                "study": study.model_dump(),
                "metrics": metrics.model_dump(),
                "qc": qc.model_dump(),
                "prediction_metadata": st.session_state.pred_meta.model_dump() if st.session_state.pred_meta else None,
                "copilot_model": copilot.model_name,
            }
            json_str = json.dumps(json_bundle, indent=2, default=str)
            st.download_button(
                label="⬇️ Download Analysis Evidence Bundle (.json)",
                data=json_str,
                file_name=f"evidence_{study.metadata.study_id}.json",
                mime="application/json",
                **STRETCH_KW,
            )
