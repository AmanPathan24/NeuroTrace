"""Pydantic data schemas and immutable contracts for NeuroTrace."""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field


class VoxelSpacing(BaseModel):
    """Voxel dimensions in millimeters (zooms)."""
    dx_mm: float = Field(..., description="Voxel spacing along X axis in mm")
    dy_mm: float = Field(..., description="Voxel spacing along Y axis in mm")
    dz_mm: float = Field(..., description="Voxel spacing along Z axis in mm")

    @property
    def voxel_volume_mm3(self) -> float:
        """Physical volume of a single voxel in mm^3."""
        return float(self.dx_mm * self.dy_mm * self.dz_mm)


class ImageDimensions(BaseModel):
    """3D Matrix dimensions."""
    dim_x: int = Field(..., description="Size along X axis (width/sagittal)")
    dim_y: int = Field(..., description="Size along Y axis (height/coronal)")
    dim_z: int = Field(..., description="Size along Z axis (slices/depth/axial)")

    @property
    def total_voxels(self) -> int:
        return self.dim_x * self.dim_y * self.dim_z

    @property
    def shape_tuple(self) -> Tuple[int, int, int]:
        return (self.dim_x, self.dim_y, self.dim_z)


class IntensityStats(BaseModel):
    """Voxel intensity distribution statistics."""
    min_value: float
    max_value: float
    mean_value: float
    std_value: float
    p01_value: float = Field(..., description="1st percentile intensity")
    p99_value: float = Field(..., description="99th percentile intensity")


class StudyMetadata(BaseModel):
    """Metadata identifying an ingested MRI study."""
    study_id: str
    filename: str
    file_size_bytes: int
    sha256_hash: str
    modality: str = Field(default="FLAIR", description="Acquisition sequence modality")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidatedStudy(BaseModel):
    """Fully validated MRI volume metadata and geometry contract."""
    metadata: StudyMetadata
    dimensions: ImageDimensions
    spacing: VoxelSpacing
    orientation: str = Field(..., description="Standard 3-letter anatomical axis orientation (e.g. LPS, RAS)")
    affine_matrix: List[List[float]] = Field(..., description="4x4 affine coordinate transformation matrix")
    intensity_stats: IntensityStats
    is_valid: bool = True
    validation_notes: List[str] = Field(default_factory=list)


class PredictionMetadata(BaseModel):
    """Metadata recorded for an inference execution run."""
    prediction_id: str
    study_id: str
    model_name: str = "NeuroSegNet 3D U-Net"
    checkpoint_file: str
    checkpoint_hash: Optional[str] = None
    device: str
    inference_seconds: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SegmentationArtifact(BaseModel):
    """Contract for a generated segmentation mask artifact."""
    prediction_id: str
    study_id: str
    mask_path: Optional[str] = None
    unique_labels: List[int] = Field(default_factory=lambda: [0, 1])
    label_map: Dict[int, str] = Field(
        default_factory=lambda: {0: "Background", 1: "Tumor / Lesion"}
    )
    metadata: PredictionMetadata


class BoundingBox3D(BaseModel):
    """3D bounding box coordinates."""
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    z_min: int
    z_max: int

    @property
    def dimensions(self) -> Tuple[int, int, int]:
        return (
            max(0, self.x_max - self.x_min + 1),
            max(0, self.y_max - self.y_min + 1),
            max(0, self.z_max - self.z_min + 1),
        )


class AnalysisMetrics(BaseModel):
    """Deterministic quantitative segmentation measurements."""
    analysis_id: str
    study_id: str
    prediction_id: str
    tumor_voxel_count: int
    total_brain_voxels: int
    tumor_volume_fraction_percent: float
    physical_volume_cm3: float
    bounding_box: Optional[BoundingBox3D] = None
    centroid_voxel: Optional[Tuple[float, float, float]] = None
    centroid_world_mm: Optional[Tuple[float, float, float]] = None
    slice_distribution: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    ground_truth_available: bool = False
    dice_score: Optional[float] = None
    iou_score: Optional[float] = None
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QCReport(BaseModel):
    """Technical quality control findings for an MRI scan and segmentation."""
    qc_id: str
    study_id: str
    prediction_id: Optional[str] = None
    is_empty_mask: bool
    brain_voxel_fraction: float
    signal_to_noise_ratio_est: float
    contrast_ratio_est: float
    is_passed: bool
    flags: List[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

