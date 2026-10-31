"""Unit tests for configuration and Pydantic contracts."""
import json
from pathlib import Path
import pytest

from config.settings import Settings, get_settings
from core.contracts import (
    VoxelSpacing,
    ImageDimensions,
    IntensityStats,
    StudyMetadata,
    ValidatedStudy,
    AnalysisMetrics,
    BoundingBox3D,
    QCReport,
)


def test_settings_loading():
    """Verify settings defaults and singleton resolution."""
    settings = get_settings()
    assert settings.app_name == "NeuroTrace"
    assert settings.in_channels == 1
    assert settings.out_channels == 2
    assert settings.base_filters == 8
    assert settings.device in ("cpu", "cuda")
    assert "flair" in settings.supported_modalities


def test_contracts_serialization():
    """Verify JSON round-trip serialization of contracts."""
    study = ValidatedStudy(
        metadata=StudyMetadata(
            study_id="study_test_123",
            filename="test_scan.nii.gz",
            file_size_bytes=10240,
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            modality="FLAIR",
        ),
        dimensions=ImageDimensions(dim_x=240, dim_y=240, dim_z=155),
        spacing=VoxelSpacing(dx_mm=1.0, dy_mm=1.0, dz_mm=1.0),
        orientation="LPS",
        affine_matrix=[
            [-1.0, 0.0, 0.0, 0.0],
            [0.0, -1.0, 0.0, 239.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        intensity_stats=IntensityStats(
            min_value=0.0,
            max_value=600.0,
            mean_value=30.0,
            std_value=70.0,
            p01_value=0.0,
            p99_value=450.0,
        ),
        is_valid=True,
    )

    json_str = study.model_dump_json()
    parsed_dict = json.loads(json_str)
    reconstructed = ValidatedStudy.model_validate(parsed_dict)

    assert reconstructed.metadata.study_id == "study_test_123"
    assert reconstructed.dimensions.total_voxels == 240 * 240 * 155
    assert reconstructed.spacing.voxel_volume_mm3 == 1.0
    assert reconstructed.affine_matrix[1][3] == 239.0


def test_analysis_metrics_contract():
    """Verify AnalysisMetrics schema."""
    metrics = AnalysisMetrics(
        analysis_id="analysis_001",
        study_id="study_001",
        prediction_id="pred_001",
        tumor_voxel_count=67692,
        total_brain_voxels=1551130,
        tumor_volume_fraction_percent=4.36,
        physical_volume_cm3=67.69,
        bounding_box=BoundingBox3D(
            x_min=50, x_max=120, y_min=60, y_max=140, z_min=30, z_max=95
        ),
        centroid_voxel=(85.0, 100.0, 62.5),
        ground_truth_available=False,
    )
    
    assert metrics.bounding_box.dimensions == (71, 81, 66)
    assert metrics.ground_truth_available is False
    assert metrics.dice_score is None

