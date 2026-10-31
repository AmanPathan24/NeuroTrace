# 🧠 NeuroTrace — Agentic Brain MRI Segmentation Analysis & Research Copilot

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-ff4b4b.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3f4f75.svg)](https://plotly.com/)
[![Tests](https://img.shields.io/badge/tests-41%20passed%20%7C%20100%25-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **"NeuroTrace — From segmentation to evidence."**

NeuroTrace is an open-source, research-grade computational neuroimaging analysis platform. It evolves raw brain MRI segmentation into an integrated scientific evidence workflow: ingesting NIfTI volumes, executing a verified 3D U-Net neural network, rendering interactive multi-planar 2D and 3D volumetric visualizations, calculating deterministic geometric measurements, running technical quality control, integrating an allowlisted **Gemma 4** research copilot, and generating reproducible PDF reports.

---

> [!IMPORTANT]
> **Research and Educational Use Only**: NeuroTrace is strictly an academic research and educational system. It does **not** provide clinical diagnoses, prognoses, surgical margins, or treatment recommendations. All measurements are automated computational estimates intended to assist scientific research.

---

## 🌟 Key Features

### 1. Ingestion & Spatial Geometry Engine
- Ingests **NIfTI** files (`.nii` and `.nii.gz`) through direct filesystem paths or in-memory streaming uploads.
- Validates 3D spatial dimensions, squeezes 4D single-channel dimensions, and rejects flat/empty arrays.
- Extracts native 4x4 spatial affine transformation matrices, voxel spacing (`dx, dy, dz` in mm), and canonical radiological orientation (e.g. `LPS`, `RAS`).
- Computes SHA256 checksums to guarantee study immutability and provenance tracking.

### 2. NeuroSegNet 3D U-Net Inference Engine
- Powered by a verified pretrained **3D U-Net** (`1,413,250` parameters, 8 base filters, 1 input channel, 2 output classes).
- Production checkpoint: `Flairbased_2/model_epoch_45 (1).pt` (validation loss `0.1756`, peak tumor validation Dice `0.4622`).
- Runs full-volume `(240, 240, 155)` inference on CPU in **~12–15 seconds** without requiring CUDA or GPU hardware.
- Exports binary segmentation masks as `.nii.gz` while strictly preserving the reference scan's spatial affine and coordinate frame.

### 3. Interactive Multi-Planar 2D Slice Viewers
- Synchronized **Axial (Z)**, **Coronal (Y)**, and **Sagittal (X)** orthogonal slice viewers built with Plotly.
- Dynamic 1st–99th percentile contrast normalization for crisp brain parenchyma visibility.
- Semi-transparent cyan tumor mask overlays with adjustable opacity sliders.
- High-contrast tumor boundary contours extracted via marching-cubes contour detection.
- Crosshair guidelines and standard anatomical direction labels (Anterior/Posterior, Left/Right, Superior/Inferior).

### 4. Interactive 3D Volume & Isosurface Rendering
- Interactive 3D visualization combining volumetric brain MRI rendering (`go.Volume`) and distinct tumor isosurface surfaces (`go.Isosurface`).
- Independent visibility toggles for brain tissue and tumor boundaries.
- User-adjustable opacity sliders, lighting shaders (ambient, diffuse, specular, and Fresnel depth), and camera presets.
- Dynamic downsampling options (`0.2x` to `0.5x`) ensuring smooth, responsive 60fps WebGL rendering in browser sessions.

### 5. Deterministic Volumetric Measurements
- **Physical Volume**: Calculated deterministically using verified voxel spacing: $\text{Volume (mL)} = \frac{\text{Tumor Voxels} \times (dx \times dy \times dz)}{1000}$.
- **Voxel Counts & Brain Fraction**: Exact tumor voxel count and percentage relative to non-zero brain volume.
- **3D Bounding Box**: Min/max coordinates and extent dimensions along X, Y, and Z.
- **Dual Centroids**: Centroid calculated in both voxel index space $(c_x, c_y, c_z)$ and scanner world coordinates in millimeters $(X_{\text{mm}}, Y_{\text{mm}}, Z_{\text{mm}})$.
- **Diagnostic Slice Distribution**: Identifies peak slices with highest tumor concentration across all three planes.
- **Missing Ground Truth Protocol**: Strictly marks reference metrics as `"Not Available"` (never fabricated or reported as 0) when no ground-truth mask is provided.

### 6. Automated Technical Quality Control
- **Empty Mask Detection**: Identifies negative findings across the scan volume.
- **Air-Boundary Overflow Check**: Flags segmentations that artificially leak outside apparent brain tissue into background air.
- **Lesion Fragmentation Analysis**: Measures disconnected tumor components via connected-component labeling and reports primary cluster ratios.
- **Signal-to-Noise Ratio (SNR) & Contrast**: Estimates background noise and tumor-to-parenchyma contrast ratio.

### 7. Google Gemma 4 Research Assistant Copilot
NeuroTrace integrates Google's **Gemma 4** models through an agentic, allowlisted computational tool architecture:
- **Supported Gemma 4 Models**:
  - `gemma-4-31b-it`: Dense 31-billion parameter instruction-tuned model. Optimized for complex neuroimaging reasoning, comparative analysis, and structured scientific report synthesis.
  - `gemma-4-26b-a4b-it`: Mixture-of-Experts (MoE) 26-billion parameter architecture (4B active parameters). Optimized for ultra-fast interactive Q&A and low-latency research guidance.
- **Agentic Allowlisted Tool Architecture**:
  - Gemma 4 interacts with the analysis pipeline exclusively through strictly validated computational tools: `validate_mri_study`, `run_neurosegnet`, `calculate_tumor_volumes`, `inspect_segmentation_quality`, and `generate_research_report`.
  - Gemma 4 cannot run arbitrary code or alter files; every calculation is performed by deterministic Python algorithms on physical voxel spacing.
- **Zero-Hallucination Evidence Grounding**:
  - Every volumetric figure ($mL$), voxel count, bounding box coordinate, slice distribution, and SNR metric cited by Gemma 4 is directly extracted from verified execution contracts.
- **Local Data Privacy Doctrine**:
  - Raw NIfTI MRI volumetric datasets remain strictly on the local machine. Gemma 4 receives only structured JSON metadata and deterministic measurements, preventing sensitive patient or subject neuroimaging data from leaving the local workstation.
- **Dual Execution Modes**:
  - **Live Google GenAI Mode**: Interacts directly with `gemma-4-31b-it` or `gemma-4-26b-a4b-it` when a Google Gemini API key is supplied.
  - **Deterministic Local Mode**: If running offline or without an API key, an internal scientific synthesis engine automatically produces structured, evidence-grounded summaries using the same verified contracts.

### 8. Publication-Grade Research PDF Reports
- Generates downloadable multi-page PDF documents via ReportLab.
- Embeds study metadata, model provenance, quantitative volumetric tables, technical QC findings, and attributed AI commentary.
- Embeds high-resolution multi-planar slice thumbnails (Axial, Coronal, Sagittal) with color-tinted tumor overlays.
- Features a two-pass numbered canvas with running headers, footers, page counts (`Page X of Y`), and research disclaimers.

---

## 🏛️ System Architecture

```text
NeuroTrace/
├── config/                  # Pydantic configuration and environment settings
│   └── settings.py          # Central configuration schema (paths, device, checkpoints)
├── core/                    # Immutable domain contracts and custom exceptions
│   ├── contracts.py         # Pydantic schemas (ValidatedStudy, AnalysisMetrics, QCReport)
│   └── errors.py            # Domain error hierarchy (CorruptedFileError, etc.)
├── imaging/                 # NIfTI ingestion, geometry validation, and normalization
│   ├── loader.py            # In-memory streaming loader and header validator
│   └── preprocessor.py      # Z-score normalization and 5D tensor formatting
├── models/                  # Neural network architecture and inference adapter
│   ├── unet3d.py            # Standalone PyTorch 3D U-Net implementation
│   ├── adapter.py           # Safe checkpoint loading and deterministic inference
│   └── exporter.py          # Geometry-preserving NIfTI mask exporter
├── analysis/                # Deterministic measurements and quality control
│   ├── measurements.py      # Physical volumes, bounding boxes, centroids, Dice/IoU
│   └── qc.py                # Automated technical QC checks (SNR, boundary, components)
├── visualization/           # Interactive 2D and 3D visualization suite
│   ├── slices_2d.py         # Multi-planar 2D orthogonal viewers with contour overlays
│   └── volume_3d.py         # 3D Plotly volume and tumor isosurface renderer
├── agents/                  # Gemma 4 research assistant integration
│   ├── tools.py             # Allowlisted computational tool execution registry
│   ├── prompts.py           # Scientific research copilot persona and system prompts
│   └── copilot.py           # Gemma 4 agent orchestration and evidence synthesis
├── reporting/               # Publication-grade PDF report generation
│   └── pdf_generator.py     # ReportLab generator with embedded slice thumbnails
├── tests/                   # Automated unit, integration, and regression tests
│   ├── unit/                # Unit test suites (loader, analysis, viz, agent, reporting)
│   └── integration/         # Integration tests (model weights, golden reference check)
├── docs/                    # Technical documentation and integration contracts
│   ├── NEUROSEGNET_INTEGRATION_CONTRACT.md
│   └── PHASE_0_RECONNAISSANCE_REPORT.md
├── requirements.txt         # Verified minimal dependencies
├── .env.example             # Configuration template
├── .gitignore               # Strict ignore rules for weights, scans, and private data
└── README.md                # Master documentation (this file)
```

---

## 🔬 Verified Golden Reference Benchmark

NeuroTrace has been empirically validated against real brain MRI scans from the BraTS20 benchmark dataset:

| Metric | Target Value | Empirical Result | Status |
|---|---|---|---|
| **Test Volume** | `BRATS/BraTS20_Training_030_flair.nii` | `(240, 240, 155)`, 1.0 mm³ spacing | ✅ Verified |
| **Model Weights** | `Flairbased_2/model_epoch_45 (1).pt` | 1,413,250 parameters (strict match) | ✅ Verified |
| **Inference Time (CPU)** | < 60 seconds | **~12.6 – 15.0 seconds** | ✅ Verified |
| **Tumor Voxel Count** | 67,692 – 67,694 voxels | **67,694 voxels** | ✅ Verified |
| **Physical Tumor Volume** | 67.69 mL (`cm³`) | **67.694 mL** | ✅ Verified |
| **Brain Volume Fraction** | 4.36% of brain volume | **4.364%** | ✅ Verified |
| **Unit, Integration & E2E Tests**| 100% Pass Rate | **41 passed / 0 failed** | ✅ Verified |

---

## 🚀 Installation & Getting Started

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 (64-bit).
- Windows, macOS, or Linux.
- 8 GB RAM minimum (16 GB recommended for 3D rendering).
- Standard CPU (CUDA GPU supported automatically when available).

### 2. Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/AmanPathan24/NeuroTrace.git
cd NeuroTrace

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the `.env.example` template to `.env`:

```bash
cp .env.example .env
```

Edit `.env` to customize settings or add your Google Gemini API key for the live Gemma 4 copilot:

```ini
NEUROTRACE_MODEL_PATH=Flairbased_2/model_epoch_45 (1).pt
NEUROTRACE_DEVICE=cpu
GEMINI_API_KEY=your_gemini_api_key_here
# Choose: gemma-4-31b-it (default) or gemma-4-26b-a4b-it
GEMMA_MODEL_ID=gemma-4-31b-it
```

*(Note: NeuroTrace functions completely offline if no API key is provided, using its deterministic scientific evidence synthesis engine).*

---

## 🧪 Running the Test Suite

Execute the comprehensive automated test suite with pytest:

```bash
pytest -v tests/
```

To run specific test categories:

```bash
# Run unit tests only
pytest -v tests/unit/

# Run model checkpoint and inference integration tests
pytest -v tests/integration/
```

---

## 💻 Running the NeuroTrace Application

Launch the Streamlit research interface:

```bash
streamlit run app.py
```

### User Workflow:
1. **Upload MRI Scan**: Drag and drop a FLAIR NIfTI scan (`.nii` or `.nii.gz`) or select one of the built-in reference BraTS volumes.
2. **Review Geometry**: Inspect matrix dimensions, voxel spacing, canonical orientation, and intensity percentiles.
3. **Execute Segmentation**: Click **Run NeuroSegNet Segmentation** (takes ~12 seconds on CPU).
4. **Inspect Visualizations**:
   - Navigate 2D Axial, Coronal, and Sagittal orthogonal slices with tumor contour overlays.
   - Rotate, pan, and zoom the interactive 3D brain volume and tumor isosurface.
5. **Analyze Quantitative Findings**: Review deterministic volumes (mL), bounding box dimensions, centroids, and technical QC flags.
6. **Consult Gemma 4 Copilot**: Ask questions about measurements, QC observations, or slice involvement.
7. **Export Artifacts**: Download the publication-grade PDF research report and the spatially aligned NIfTI segmentation mask.

---

## 🔒 Privacy & Data Protection Policy

- **Zero Remote MRI Transmission**: Raw MRI scan files and voxel arrays are processed strictly locally. No patient imaging data is ever uploaded to external cloud APIs.
- **Protected Weight & Data Assets**: Large model weights (`*.pt`, `*.h5`) and medical scans (`*.nii`, `*.nii.gz`) are permanently excluded from version control via `.gitignore`.
- **Anonymized Lineage**: Study records utilize generated opaque identifiers (`study_XXXXXXXX`) rather than patient names.

---

## 📜 License & Citation

NeuroTrace is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

If you use NeuroTrace in academic research, please cite:

```bibtex
@software{neurotrace2026,
  author = {NeuroTrace Development Team},
  title = {NeuroTrace: Agentic Brain MRI Segmentation Analysis & Research Copilot},
  year = {2026},
  publisher = {GitHub},
  url = {https://github.com/AmanPathan24/NeuroTrace}
}
```

