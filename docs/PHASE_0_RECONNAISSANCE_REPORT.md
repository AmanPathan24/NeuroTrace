# NeuroTrace — Phase 0 Reconnaissance & Audit Report

**Date**: 2026-10-31  
**Author**: Lead Software Architect & ML Engineering Team  
**Status**: Completed — Awaiting User Approval to Proceed to Phase 1  

---

## 1. Executive Summary

This reconnaissance report documents the comprehensive audit of the NeuroTrace codebase, pretrained checkpoints, data assets, and execution environment. 

All primary technical assumptions have been empirically tested and verified against the actual files in the workspace:
1. **The Model**: The actual trained model is a **single-modality 3D U-Net** (`in_channels=1`, `out_channels=2`, `base_filters=8`, total parameters: 1,413,250), taking **FLAIR NIfTI** brain MRI volumes. It is **not** a 4-modality model.
2. **The Best Checkpoint**: `Flairbased_2/model_epoch_45 (1).pt` achieves the lowest validation loss (0.1756) and highest validation Dice score (0.4622) among all 4 available checkpoints. Strict state-dict loading succeeded with **0 missing and 0 unexpected keys**.
3. **Execution Feasibility**: Full volume CPU inference executes in **12.60 seconds** on standard hardware without GPU requirement, producing a crisp, deterministic binary tumor mask.
4. **Legacy Discrepancies**: The documentation claims regarding "clinical prediction" via H5 models (`brain_tumor_type.h5` and `brain_tumor_growth.h5`) depend on missing source files (`clinical_form.py`, `clinical_models.py`, `theme_manager.py`) and unverified pseudo-clinical diagnosis prompts. Per product vision, these will be completely separated/deprecated in favor of a rigorous, deterministic **"From segmentation to evidence"** scientific workflow.
5. **Git Structure**: Initialized clean Git tracking with branch `develop` and feature branch `feature/phase-0-repository-audit`. All sensitive weights, NIfTI scans, and reference directories are protected via `.gitignore`.

---

## 2. Repository & File Inventory Audit

### 2.1 Directory Structure
```text
D:\Projects\NeuroTrace\
├── BRATS/                                 # 9 BraTS20 FLAIR NIfTI scans (Training 001-030)
├── Flairbased_2/                          # 4 trained PyTorch checkpoints (epochs 20, 45, 50, 55)
├── models/                                # 2 legacy H5 models (tumor type, tumor growth)
├── reference_material/                    # Original reference source files
│   ├── model.py                           # Reference 3D U-Net definition & inference
│   ├── tumor_segmentation.py              # Object-oriented wrapper for UNet3D
│   ├── Vis3d.py                           # Plotly 3D volume & isosurface visualization
│   ├── VisSlices.py                       # Matplotlib slice & orthogonal interactive viewer
│   ├── main.py                            # Minimal end-to-end CLI script
│   ├── app.py                             # Legacy Streamlit app (contains broken imports)
│   ├── ai_report.py                       # Legacy Gemini REST API caller with clinical prompts
│   ├── FINAL_STATUS.md                    # Historical status notes
│   ├── README.md                          # Original project documentation
│   └── README_ENHANCED.md                 # Enhanced documentation with clinical claims
├── NeuroTrace_Antigravity_Pack/           # Architecture, PRD, and skill specifications
└── NeuroTrace_Antigravity_Starter_Pack/   # Empty directory
```

### 2.2 Python Environment & Dependencies
- **OS**: Windows 11 AMD64
- **Python**: 3.13.1
- **PyTorch**: 2.8.0+cpu (`torch.cuda.is_available() == False` — CPU execution verified)
- **NumPy**: 2.2.2
- **SciPy**: 1.15.1
- **Scikit-Image**: 0.25.0
- **Streamlit**: 1.50.0
- **Plotly**: 6.2.0
- **Pydantic**: 2.11.9
- **ReportLab**: 4.2.5
- **Pytest**: 9.0.3
- **Google GenAI SDK**: installed
- **NiBabel**: Installed `nibabel==5.4.2` to support full NIfTI I/O and header inspection.

---

## 3. Model Architecture & Checkpoint Compatibility Report

### 3.1 Model Architecture Specification
From `reference_material/model.py`:
```python
class UNet3D(nn.Module):
    def __init__(self, in_channels=1, out_channels=2, base_filters=8, dropout=0.2):
```
- **Encoder**: 4 stages (8 -> 16 -> 32 -> 64 filters) with `ConvBlock3D` (Conv3d 3x3x3 -> BatchNorm3d -> Conv3d 3x3x3 -> BatchNorm3d -> ReLU -> Dropout3d) and `MaxPool3d(2)`.
- **Bottleneck**: 128 filters.
- **Decoder**: 4 stages (64 -> 32 -> 16 -> 8 filters) with `ConvTranspose3d(kernel_size=2, stride=2)` and skip connections aligned using `crop_or_pad()`.
- **Head**: `nn.Conv3d(base_filters, out_channels, kernel_size=1)`.
- **Total Parameters**: 1,413,250 (5.65 MB fp32 weights).

### 3.2 Comprehensive Checkpoint Audit

All 4 checkpoints in `Flairbased_2/` were loaded on CPU and evaluated:

| Checkpoint File | Epoch | File Size | Train Loss | Val Loss | Val Dice [Bg, Tumor] | Strict Load Status |
|---|---|---|---|---|---|---|
| `model_epoch_20.pt` | 20 | 16.29 MB | 0.1287 | 0.1854 | [0.9970, 0.4256] | Success (0 missing / 0 unexpected) |
| **`model_epoch_45 (1).pt`** | **45** | **16.29 MB** | **0.1159** | **0.1756** | **[0.9971, 0.4622]** | **Success (0 missing / 0 unexpected)** |
| `model_epoch_50.pt` | 50 | 16.29 MB | 0.1183 | 0.1873 | [0.9971, 0.4265] | Success (0 missing / 0 unexpected) |
| `model_epoch_55.pt` | 55 | 16.29 MB | 0.1171 | 0.1926 | [0.9971, 0.4078] | Success (0 missing / 0 unexpected) |

**Conclusion**: `model_epoch_45 (1).pt` is verified as the optimal production checkpoint. Validation loss reaches its minimum at epoch 45 (0.1756) and validation Dice peaks at 0.4622 for the tumor class before beginning to overfit in epochs 50 and 55.

### 3.3 Golden Inference Smoke Test
Empirical smoke test executed on `BRATS/BraTS20_Training_030_flair.nii`:
- **Input Dimensions**: `(240, 240, 155)`, voxel spacing `1.0 x 1.0 x 1.0` mm, orientation LPS/RAS.
- **Preprocessing**: Volume Z-score normalization `(img - mean) / (std + 1e-8)`.
- **Inference Runtime**: **12.60 seconds** on standard CPU.
- **Logits Tensor**: Shape `(1, 2, 240, 240, 155)`.
- **Predicted Mask**: Shape `(240, 240, 155)`, binary values `{0, 1}`.
- **Quantitative Findings**:
  - Tumor Voxels: **67,692**
  - Brain Foreground Voxels (>0): 1,551,130
  - Tumor Volume Fraction: **4.36%**
  - Physical Tumor Volume: **67.69 mL** (using verified 1.0 mm³ voxel spacing)

---

## 4. Existing Visualization & UI Analysis

### 4.1 3D Visualization (`Vis3d.py`)
- **Mechanism**: Plotly `go.Volume` for FLAIR scan + `go.Isosurface` (`isomin=0.5, isomax=1.0`) for tumor segmentation.
- **Downsampling**: Resizes volume to 0.25 scale (60 x 60 x 39) with `skimage.transform.resize` to ensure interactive rendering performance in the browser.
- **Assessment**: Functionally sound and visually clean. In NeuroTrace, we will preserve this approach and enhance it with:
  1. Dynamic resolution selection (0.2x fast preview, 0.35x detailed, 0.5x high-res).
  2. Independent opacity and visibility controls for brain volume and tumor surface.
  3. Interactive coordinate-to-world millimeter spatial alignment.
  4. Camera presets (axial, coronal, sagittal, isometric).

### 4.2 2D Visualization (`VisSlices.py`)
- **Mechanism**: Matplotlib orthogonal viewer (Axial, Coronal, Sagittal) with slider widgets and contour overlays.
- **Limitations**: Calls `plt.show()`, which spawns a blocking desktop GUI window that fails inside web Streamlit.
- **Assessment**: In NeuroTrace, we will migrate 2D orthogonal navigation to native Streamlit reactive sliders and Plotly interactive heatmaps/contour overlays with synchronized crosshairs.

### 4.3 Legacy Streamlit Application (`app.py`)
- **Findings**: `app.py` in `reference_material` contains broken imports:
  ```python
  from clinical_form import get_clinical_form
  from clinical_models import get_clinical_predictor
  from theme_manager import get_theme_manager
  from pdf_report_generator import MedicalReportGenerator
  ```
  None of these 4 files exist in the repository.
- **Legacy Clinical Claims**: The app attempted to ask 16 clinical questions (smoking, diabetes, etc.) and predict "benign vs malignant" and "growth rate" with H5 models.
- **Resolution**: As directed by the user, NeuroTrace will discard this unvalidated pseudo-clinical form and focus on verifiable **"From segmentation to evidence"** scientific and imaging metrics.

---

## 5. Proposed Architecture

NeuroTrace will be structured as a clean, modular Python application:

```text
neurotrace/
├── config/
│   ├── __init__.py
│   └── settings.py              # Pydantic-based configuration (paths, device, thresholds)
├── core/
│   ├── __init__.py
│   ├── contracts.py             # Typed Pydantic schemas (Study, Segmentation, Analysis, QC)
│   └── errors.py                # Typed domain exceptions
├── imaging/
│   ├── __init__.py
│   ├── loader.py                # NIfTI loader & geometry/orientation validator
│   └── preprocessor.py          # Z-score normalization & spatial preservation
├── models/
│   ├── __init__.py
│   ├── unet3d.py                # Pure PyTorch 3D U-Net implementation
│   └── adapter.py               # Safe checkpoint loading & inference engine
├── analysis/
│   ├── __init__.py
│   ├── measurements.py          # Deterministic volume, bounding box, centroid calculations
│   └── qc.py                    # Quality control checks (air-voxel ratio, contrast, SNR)
├── visualization/
│   ├── __init__.py
│   ├── slices_2d.py             # Streamlit/Plotly 2D orthogonal multi-planar viewer
│   └── volume_3d.py             # Streamlit/Plotly interactive 3D volume & isosurface viewer
├── agents/
│   ├── __init__.py
│   ├── tools.py                 # Allowlisted deterministic research tools for Gemma 4
│   ├── prompts.py               # Controlled system prompt (research copilot persona)
│   └── copilot.py               # Gemma 4 agent orchestration via Google GenAI SDK
├── reporting/
│   ├── __init__.py
│   └── pdf_generator.py         # ReportLab PDF generator (deterministic metrics + figures)
├── ui/
│   ├── __init__.py
│   ├── components.py            # Reusable UI widgets and layout cards
│   └── views.py                 # Multi-stage Streamlit workflow views
├── tests/
│   ├── unit/                    # Unit tests for contracts, loader, analysis, QC
│   ├── integration/             # Model loading and inference tests
│   └── e2e/                     # End-to-end workflow verification
├── app.py                       # Main Streamlit application entry point
├── requirements.txt             # Verified minimal dependencies
├── .env.example                 # Environment configuration template
└── .gitignore                   # Protected files specification
```

---

## 6. Updated Phase-Wise Implementation Plan & Acceptance Criteria

### Phase 1 — Foundation and MRI Ingestion
- **Scope**: Project structure, typed contracts (`core/contracts.py`), configuration management (`config/settings.py`), NIfTI loading and validation (`imaging/loader.py`).
- **Acceptance Criteria**:
  - Valid NIfTI files (`BRATS/*.nii`) load with complete geometry, affine, and voxel spacing extracted.
  - Corrupted, non-3D, or non-NIfTI files trigger structured, informative domain errors.
  - Voxel dimensions and spatial coordinates are rigorously preserved.
  - Comprehensive unit tests pass.

### Phase 2 — Existing Model Integration
- **Scope**: Model architecture (`models/unet3d.py`) and inference adapter (`models/adapter.py`).
- **Acceptance Criteria**:
  - `model_epoch_45 (1).pt` loads cleanly on CPU/GPU without missing/unexpected keys.
  - Inference executes within 15 seconds on CPU for standard 240x240x155 volumes.
  - Output binary mask matches verified golden results (67,692 voxels on BraTS20_030).
  - Geometry is preserved on export to NIfTI mask.
  - No mock/synthetic predictions used.

### Phase 3 — Deterministic Analysis and QC
- **Scope**: Deterministic measurements (`analysis/measurements.py`) and technical QC (`analysis/qc.py`).
- **Acceptance Criteria**:
  - Exact voxel count, physical volume (mL), 3D bounding box, centroid, and slice distribution calculated.
  - Missing ground-truth handling: Dice/IoU correctly reported as "N/A" (never reported as 0 or fabricated).
  - Automated QC checks: empty mask detection, volume outlier detection, brain-mask boundary validation.
  - Unit tests verify calculations on synthetic and real arrays.

### Phase 4 — Interactive Visualization
- **Scope**: 2D multi-planar viewer (`visualization/slices_2d.py`) and 3D volume/surface viewer (`visualization/volume_3d.py`).
- **Acceptance Criteria**:
  - Synchronized Axial, Coronal, and Sagittal 2D viewers with opacity slider and tumor contour overlays inside Streamlit.
  - Interactive 3D Plotly rendering with semi-transparent brain volume and distinct tumor isosurface.
  - Independent visibility/opacity toggles for brain and tumor.
  - Fast, responsive user experience without blocking GUI popups.

### Phase 5 — Gemma 4 Agent Integration
- **Scope**: Allowlisted research tools (`agents/tools.py`) and agent copilot (`agents/copilot.py`).
- **Acceptance Criteria**:
  - Gemma 4 interacts only through allowlisted tools (`validate_mri_study`, `run_neurosegnet`, `calculate_tumor_volumes`, `inspect_segmentation_quality`).
  - Agent answers strictly cite deterministic metrics from the analysis engine.
  - No arbitrary code execution; raw MRI data remains local by default.
  - Clear attribution marking AI commentary as generated assistance.

### Phase 6 — Research Reporting
- **Scope**: Research PDF generation (`reporting/pdf_generator.py`).
- **Acceptance Criteria**:
  - Downloadable multi-page PDF containing study metadata, deterministic volume measurements, QC findings, 2D slice thumbnails, and Gemma research summary.
  - Prominent "Research and Educational Use Only" disclaimer on every page.
  - Exportable NIfTI mask and structured JSON analysis bundle.

### Phase 7 — Integration, Testing and Release
- **Scope**: End-to-end workflow verification, documentation, and release packaging.
- **Acceptance Criteria**:
  - Clean application launch via `streamlit run app.py`.
  - Full end-to-end test suite passes.
  - Zero sensitive patient data, checkpoints, or secrets committed in Git.
  - Complete README with reproduction guide and architecture documentation.

---

## 7. Risks, Unknowns, and Recommendations

1. **Hardware Constraints**: The target environment is Windows on CPU. Full-volume 3D U-Net inference on CPU takes ~12.6 seconds. This is completely viable for interactive research sessions, but progress indicators (`st.spinner`) and caching (`@st.cache_resource`) must be used.
2. **Interactive 3D Performance**: Full-resolution 3D volume rendering of 240x240x155 in Plotly creates large WebGL payloads. The 0.25x downsampling strategy proven in `Vis3d.py` keeps rendering fast (<1s load time) and should remain default, with optional user toggles for higher resolution.
3. **Absence of Ground Truth**: BraTS sample files in `BRATS/` provide FLAIR scans only, without ground-truth `_seg.nii` files. NeuroTrace will cleanly display ground-truth metrics as "Not Available / No Reference Mask Provided" rather than inventing numbers.

---

## 8. Git Commit Log for Phase 0

- `develop` branch created from `main`.
- `feature/phase-0-repository-audit` branch created and active.
- Commit planned: `docs: complete Phase 0 reconnaissance and model integration contract`
