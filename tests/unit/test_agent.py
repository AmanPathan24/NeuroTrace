"""Unit tests for Gemma 4 research agent, allowlisted tools, and copilot."""
from pathlib import Path
import numpy as np
import pytest

from agents.tools import ResearchToolRegistry
from agents.copilot import GemmaResearchCopilot
from imaging.loader import NiftiLoader
from analysis.measurements import calculate_tumor_measurements
from analysis.qc import inspect_segmentation_quality


@pytest.fixture
def populated_registry():
    """Create a registry pre-populated with a valid study session."""
    registry = ResearchToolRegistry()
    scan_path = Path("BRATS/BraTS20_Training_001_flair.nii")
    if not scan_path.exists():
        pytest.skip(f"Reference scan {scan_path} not found.")

    raw_data, nii_img, study = NiftiLoader.load_from_path(scan_path, study_id="study_test_001")
    dummy_mask = np.zeros_like(raw_data, dtype=np.uint8)
    dummy_mask[100:120, 100:120, 70:85] = 1  # 20 * 20 * 15 = 6000 voxels

    metrics = calculate_tumor_measurements(
        pred_mask=dummy_mask,
        raw_volume=raw_data,
        voxel_spacing=study.spacing,
        affine=np.array(study.affine_matrix),
        study_id="study_test_001",
        prediction_id="pred_test_001",
    )
    qc = inspect_segmentation_quality(dummy_mask, raw_data, study_id="study_test_001")

    registry.register_study_session(
        study=study,
        raw_volume=raw_data,
        pred_mask=dummy_mask,
        metrics=metrics,
        qc=qc,
    )
    return registry


def test_tool_registry_allowlist(populated_registry):
    """Verify tool allowlist enforcement and rejection of unpermitted tools."""
    # Permitted tool execution
    res = populated_registry.execute_tool(
        "calculate_tumor_volumes", {"study_id": "study_test_001"}
    )
    assert res["status"] == "success"
    assert res["tumor_voxel_count"] == 6000
    assert res["physical_volume_cm3_mL"] == 6.0

    # Unpermitted tool rejection
    forbidden_res = populated_registry.execute_tool(
        "execute_arbitrary_shell_command", {"command": "dir"}
    )
    assert forbidden_res["status"] == "error"
    assert "Security violation" in forbidden_res["error"]


def test_inspect_qc_tool(populated_registry):
    """Verify inspect_segmentation_quality tool output."""
    res = populated_registry.execute_tool(
        "inspect_segmentation_quality", {"study_id": "study_test_001"}
    )
    assert res["status"] == "success"
    assert "is_passed" in res
    assert "signal_to_noise_ratio_est" in res


def test_copilot_synthesize_summary(populated_registry):
    """Verify deterministic research summary generation."""
    copilot = GemmaResearchCopilot(tool_registry=populated_registry)
    summary = copilot.synthesize_research_summary("study_test_001")

    assert "6.00 mL" in summary
    assert "6,000 voxels" in summary
    assert "FLAIR" in summary
    assert "Disclaimer: NeuroTrace is an academic research" in summary


def test_copilot_targeted_queries(populated_registry):
    """Verify targeted user questions about volume and QC."""
    copilot = GemmaResearchCopilot(tool_registry=populated_registry)

    # Volume query
    vol_reply = copilot.chat("What is the measured tumor volume and voxel count?", study_id="study_test_001")
    assert "6.00 mL" in vol_reply
    assert "6,000" in vol_reply

    # QC query
    qc_reply = copilot.chat("Show me the technical quality control findings", study_id="study_test_001")
    assert "Technical Quality Control" in qc_reply
    assert "Gate Passed" in qc_reply

