"""NeuroTrace — Agentic Brain MRI Segmentation Analysis & Research Copilot.
Main Streamlit Application.
"""
import io
import os
import glob
import gzip
import inspect
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import nibabel as nib
import streamlit as st

# Forward and backward compatible stretch width kwargs for Streamlit
HAS_WIDTH_ARG = "width" in inspect.signature(st.button).parameters
STRETCH_KW = {"width": "stretch"} if HAS_WIDTH_ARG else {"use_container_width": True}

# Configure page settings
st.set_page_config(
    page_title="NeuroTrace — Brain MRI Research Copilot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Medical Research CSS styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #38bdf8;
        font-weight: 600;
        margin-bottom: 15px;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #334155;
        margin-bottom: 10px;
    }
    .metric-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-lbl {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
    }
    .disclaimer-banner {
        background-color: rgba(30, 41, 59, 0.7);
        border-left: 3px solid #38bdf8;
        padding: 8px 12px;
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 12px;
        border-radius: 4px;
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
    st.markdown("### 🧠 NeuroTrace")
    st.markdown("*From segmentation to evidence.*")
    st.divider()

    st.markdown("#### 1. Ingest Brain MRI Scan")
    input_source = st.radio("Source:", ["Sample BraTS Volume", "Upload NIfTI (.nii/.nii.gz)"])

    selected_file_path = None
    uploaded_file = None

    if input_source == "Sample BraTS Volume":
        sample_scans = sorted(glob.glob("BRATS/*.nii"))
        if sample_scans:
            scan_options = {Path(p).name: p for p in sample_scans}
            chosen_name = st.selectbox("Select Benchmark Scan:", list(scan_options.keys()))
            selected_file_path = scan_options[chosen_name]
        else:
            st.warning("No sample scans found in BRATS/ directory.")
    else:
        uploaded_file = st.file_uploader(
            "Upload Brain MRI Scan", type=["nii", "gz"], help="Supports .nii and .nii.gz"
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
                    st.error("Please provide or select an MRI scan.")
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
                st.success(f"Study `{study.metadata.study_id}` loaded successfully!")
        except Exception as e:
            st.error(f"Ingestion failed: {e}")

    st.divider()
    st.markdown("#### 2. Model & Execution")
    model_info = adapter.get_model_info()
    st.markdown(f"- **Architecture**: 3D U-Net (8 filters)")
    st.markdown(f"- **Parameters**: `{model_info['total_parameters']:,}`")
    st.markdown(f"- **Checkpoint**: `Epoch 45`")
    st.markdown(f"- **Device**: `{model_info['device'].upper()}`")

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
    st.markdown("#### 3. Gemma 4 Copilot Config")
    selected_gemma = st.selectbox(
        "Gemma 4 Model:",
        ["gemma-4-31b-it", "gemma-4-26b-a4b-it"],
        index=0,
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
        st.success(f"🟢 Gemma 4 Online (`{selected_gemma}`)")
    else:
        st.info(f"🟡 Local Grounding Mode (`{selected_gemma}`)")

    st.divider()
    st.caption("NeuroTrace v1.0 • Research Platform")

# ----------------- MAIN WORKSPACE -----------------
st.markdown('<p class="main-header">NeuroTrace Research Workspace</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automated Brain MRI 3D U-Net Segmentation & Evidence Synthesis</p>', unsafe_allow_html=True)
st.markdown(
    '<div class="disclaimer-banner"><b>Academic Research Notice</b>: NeuroTrace is an educational and scientific research system. '
    'Not for clinical diagnosis, prognosis, or surgical treatment planning.</div>',
    unsafe_allow_html=True,
)

if st.session_state.study is None:
    st.info("👈 Select a sample BraTS volume or upload a NIfTI scan in the sidebar to begin.")
    st.stop()

study = st.session_state.study
raw_vol = st.session_state.raw_volume
pred_mask = st.session_state.pred_mask
metrics = st.session_state.metrics
qc = st.session_state.qc

# Top KPI Highlights if segmentation is done
if metrics is not None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-val">{metrics.physical_volume_cm3:.2f} mL</div>'
            f'<div class="metric-lbl">Tumor Physical Volume</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-val">{metrics.tumor_voxel_count:,}</div>'
            f'<div class="metric-lbl">Segmented Voxels</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-val">{metrics.tumor_volume_fraction_percent:.2f}%</div>'
            f'<div class="metric-lbl">Brain Volume Fraction</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        qc_status = "PASSED" if qc.is_passed else "FLAGGED"
        color = "#22c55e" if qc.is_passed else "#ef4444"
        st.markdown(
            f'<div class="metric-card"><div class="metric-val" style="color: {color};">{qc_status}</div>'
            f'<div class="metric-lbl">Quality Control Gate</div></div>',
            unsafe_allow_html=True,
        )

# Workspace Navigation Tabs
tabs = st.tabs([
    "📊 Study & Validation",
    "🔍 2D Multi-Planar Viewer",
    "🧊 3D Volume & Surface",
    "📈 Quantitative Measurements & QC",
    "🤖 Gemma 4 Research Copilot",
    "📄 Research Report & Export",
])

# ----- TAB 1: Study & Validation -----
with tabs[0]:
    st.markdown("### Verified Study & Geometry Metadata")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Study Identifier**: `{study.metadata.study_id}`")
        st.markdown(f"**Filename**: `{study.metadata.filename}`")
        st.markdown(f"**Acquisition Modality**: `{study.metadata.modality}`")
        st.markdown(f"**Matrix Dimensions**: `{study.dimensions.dim_x} × {study.dimensions.dim_y} × {study.dimensions.dim_z}`")
        st.markdown(f"**Total Scan Voxels**: `{study.dimensions.total_voxels:,}`")
    with col_b:
        st.markdown(f"**Voxel Spacing (Zooms)**: `{study.spacing.dx_mm:.2f} × {study.spacing.dy_mm:.2f} × {study.spacing.dz_mm:.2f}` mm")
        st.markdown(f"**Voxel Unit Volume**: `{study.spacing.voxel_volume_mm3:.3f}` mm³")
        st.markdown(f"**Canonical Orientation**: `{study.orientation}`")
        st.markdown(f"**SHA256 Hash**: `{study.metadata.sha256_hash[:24]}...`")
        st.markdown(f"**Intensity Range**: `[{study.intensity_stats.min_value:.1f}, {study.intensity_stats.max_value:.1f}]` (Mean: `{study.intensity_stats.mean_value:.1f}`)")

    st.markdown("#### Affine Transformation Matrix (4×4)")
    st.dataframe(np.array(study.affine_matrix), **STRETCH_KW)

# ----- TAB 2: 2D Multi-Planar Viewer -----
with tabs[1]:
    st.markdown("### Interactive 2D Orthogonal Viewers")
    dim_x, dim_y, dim_z = raw_vol.shape

    c_opts1, c_opts2, c_opts3 = st.columns(3)
    with c_opts1:
        mask_opacity = st.slider("Mask Opacity", min_value=0.0, max_value=1.0, value=0.45, step=0.05)
    with c_opts2:
        show_contours = st.checkbox("Show Tumor Contours", value=True)
    with c_opts3:
        show_crosshairs = st.checkbox("Show Center Guidelines", value=False)

    view_mode = st.radio("Display Mode", ["Synchronized 3-Plane View", "Single High-Res Plane"], horizontal=True)

    if view_mode == "Synchronized 3-Plane View":
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            z_idx = st.slider("Axial (Z)", 0, dim_z - 1, dim_z // 2)
        with col_s2:
            y_idx = st.slider("Coronal (Y)", 0, dim_y - 1, dim_y // 2)
        with col_s3:
            x_idx = st.slider("Sagittal (X)", 0, dim_x - 1, dim_x // 2)

        fig_trio = create_orthogonal_trio_figure(
            mri_volume=raw_vol,
            pred_mask=pred_mask,
            axial_idx=z_idx,
            coronal_idx=y_idx,
            sagittal_idx=x_idx,
            show_mask=True,
            mask_opacity=mask_opacity,
            show_contours=show_contours,
        )
        st.plotly_chart(fig_trio, use_container_width=True)
    else:
        chosen_plane = st.selectbox("Select Plane:", ["Axial", "Coronal", "Sagittal"])
        max_idx = dim_z - 1 if chosen_plane == "Axial" else (dim_y - 1 if chosen_plane == "Coronal" else dim_x - 1)
        slice_idx = st.slider(f"{chosen_plane} Slice Index", 0, max_idx, max_idx // 2)

        crosshair_pt = (raw_vol.shape[0] // 2, raw_vol.shape[1] // 2) if show_crosshairs else None
        fig_single = create_orthogonal_slice_figure(
            mri_volume=raw_vol,
            pred_mask=pred_mask,
            plane=chosen_plane.lower(),
            slice_idx=slice_idx,
            show_mask=True,
            mask_opacity=mask_opacity,
            show_contours=show_contours,
            crosshair=crosshair_pt,
        )
        st.plotly_chart(fig_single, use_container_width=True)

# ----- TAB 3: 3D Volume & Surface -----
with tabs[2]:
    st.markdown("### Interactive 3D Brain & Tumor Isosurface")
    c3d_1, c3d_2, c3d_3, c3d_4 = st.columns(4)
    with c3d_1:
        res_scale = st.select_slider(
            "Rendering Resolution",
            options=[0.15, 0.20, 0.25, 0.35],
            value=0.25,
            format_func=lambda x: f"{int(x*100)}% ({'Fast' if x <= 0.2 else ('Standard' if x == 0.25 else 'Detailed')})",
        )
    with c3d_2:
        show_mri_3d = st.checkbox("Show Brain Volume", value=True)
        mri_op = st.slider("Brain Opacity", 0.05, 0.5, 0.10, 0.05) if show_mri_3d else 0.1
    with c3d_3:
        show_tumor_3d = st.checkbox("Show Tumor Surface", value=True)
        tumor_op = st.slider("Tumor Opacity", 0.1, 1.0, 0.85, 0.05) if show_tumor_3d else 0.85
    with c3d_4:
        tumor_cscale = st.selectbox("Tumor Color", ["Blues", "Electric", "Hot", "Viridis"])

    with st.spinner("Generating 3D interactive volume..."):
        fig_3d = create_3d_volume_figure(
            mri_volume=raw_vol,
            pred_mask=pred_mask,
            scale=res_scale,
            show_mri=show_mri_3d,
            show_tumor=show_tumor_3d,
            mri_opacity=mri_op,
            tumor_opacity=tumor_op,
            tumor_colorscale=tumor_cscale,
        )
        st.plotly_chart(fig_3d, use_container_width=True)

# ----- TAB 4: Quantitative Measurements & QC -----
with tabs[3]:
    st.markdown("### Quantitative Analysis & Technical QC")
    if metrics is None:
        st.info("Run segmentation in the sidebar to generate quantitative analysis.")
    else:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("#### Volumetric Measurements")
            st.markdown(f"- **Physical Tumor Volume**: `{metrics.physical_volume_cm3:.3f} mL (cm³)`")
            st.markdown(f"- **Tumor Voxel Count**: `{metrics.tumor_voxel_count:,} voxels`")
            st.markdown(f"- **Total Non-Zero Brain Voxels**: `{metrics.total_brain_voxels:,} voxels`")
            st.markdown(f"- **Tumor Fraction of Brain**: `{metrics.tumor_volume_fraction_percent:.3f}%`")
            if metrics.bounding_box:
                bb = metrics.bounding_box
                st.markdown(f"- **3D Bounding Box**: X: `[{bb.x_min}, {bb.x_max}]`, Y: `[{bb.y_min}, {bb.y_max}]`, Z: `[{bb.z_min}, {bb.z_max}]`")
                st.markdown(f"- **Lesion Extents**: `{bb.dimensions[0]} × {bb.dimensions[1]} × {bb.dimensions[2]}` voxels")
            if metrics.centroid_voxel and metrics.centroid_world_mm:
                st.markdown(f"- **Centroid (Index Coordinates)**: `{metrics.centroid_voxel}`")
                st.markdown(f"- **Centroid (Scanner World Coordinates)**: `{metrics.centroid_world_mm} mm`")

        with col_m2:
            st.markdown("#### Quality Control Evaluation")
            st.markdown(f"- **Quality Gate**: `{'PASSED' if qc.is_passed else 'FLAGGED'}`")
            st.markdown(f"- **Estimated SNR**: `{qc.signal_to_noise_ratio_est:.2f}`")
            st.markdown(f"- **Tumor-to-Brain Contrast Ratio**: `{qc.contrast_ratio_est:.2f}`")
            st.markdown(f"- **Brain Fraction of Scan**: `{qc.brain_voxel_fraction*100:.1f}%`")
            st.markdown(f"- **Empty Mask Finding**: `{'Negative (No Lesion)' if qc.is_empty_mask else 'Positive (Tumor Present)'}`")

            st.markdown("**Quality Observations & Flags**:")
            if qc.flags:
                for flag in qc.flags:
                    st.warning(f"• {flag}")
            else:
                st.success("• No anomalous boundary leakage or fragmentation detected.")

# ----- TAB 5: Gemma 4 Research Copilot -----
with tabs[4]:
    st.markdown("### 🤖 Google Gemma 4 Research Copilot")
    st.caption(
        f"Active Model: `{copilot.model_name}` | Mode: **{'Live GenAI API Connected' if copilot.client else 'Local Deterministic Tool Grounding (Zero Hallucination)'}**"
    )
    st.markdown(
        '<div style="background-color: rgba(14, 165, 233, 0.08); border-left: 3px solid #0284c7; padding: 10px 14px; border-radius: 4px; margin-bottom: 12px; font-size: 0.85rem;">'
        '<b>Gemma 4 Evidence Grounding Architecture</b>: Powered by Google Gemma 4 (<code>gemma-4-31b-it</code> / <code>gemma-4-26b-a4b-it</code>). '
        'The agent interacts strictly with allowlisted computational tools (<code>calculate_tumor_volumes</code>, <code>inspect_segmentation_quality</code>, <code>validate_mri_study</code>). '
        'All reported measurements originate from physical voxel geometries—preventing numerical hallucination and ensuring local MRI privacy.'
        '</div>',
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

    user_input = st.chat_input("Ask the research assistant about this MRI analysis...") or selected_prompt

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing verified evidence..."):
                reply = copilot.chat(user_input, study_id=study.metadata.study_id)
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ----- TAB 6: Research Report & Export -----
with tabs[5]:
    st.markdown("### Reproducible Research Export")
    if metrics is None or qc is None:
        st.info("Run segmentation analysis to enable report generation and exports.")
    else:
        col_rep1, col_rep2 = st.columns(2)
        with col_rep1:
            st.markdown("#### 📄 Publication-Grade PDF Report")
            st.markdown("Generates a multi-page PDF document containing study metadata, 3D U-Net provenance, deterministic volume tables, QC findings, embedded multi-planar figures, and Gemma 4 commentary.")

            if st.button("Generate PDF Research Report", type="primary"):
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
                    )
                    st.success("PDF Report compiled successfully!")

        with col_rep2:
            st.markdown("#### 📦 NIfTI Mask & JSON Analysis Bundle")
            st.markdown("Export the spatially aligned binary segmentation mask as a compressed NIfTI file (`.nii.gz`) preserving native affine coordinates.")

            # Export NIfTI mask purely in-memory preserving native affine and geometry
            new_header = st.session_state.nii_img.header.copy()
            new_header.set_data_dtype(np.uint8)
            seg_nii = nib.Nifti1Image(
                dataobj=pred_mask.astype(np.uint8),
                affine=st.session_state.nii_img.affine,
                header=new_header,
            )
            compressed_nii_bytes = gzip.compress(seg_nii.to_bytes())

            st.download_button(
                label="⬇️ Download Segmentation Mask (.nii.gz)",
                data=compressed_nii_bytes,
                file_name=f"segmentation_{study.metadata.study_id}.nii.gz",
                mime="application/gzip",
            )

            # JSON Bundle
            json_bundle = {
                "study": study.model_dump(),
                "metrics": metrics.model_dump(),
                "qc": qc.model_dump(),
                "prediction_metadata": st.session_state.pred_meta.model_dump() if st.session_state.pred_meta else None,
            }
            st.download_button(
                label="⬇️ Download JSON Analysis Metadata",
                data=str(json_bundle),
                file_name=f"analysis_{study.metadata.study_id}.json",
                mime="application/json",
            )

