"""Core module providing data contracts and exceptions for NeuroTrace."""
from core.errors import (
    NeuroTraceError,
    InvalidFileFormatError,
    CorruptedFileError,
    InvalidDimensionsError,
    MissingModalityError,
    GeometryValidationError,
    InferenceError,
)
from core.contracts import (
    VoxelSpacing,
    ImageDimensions,
    IntensityStats,
    StudyMetadata,
    ValidatedStudy,
    PredictionMetadata,
    SegmentationArtifact,
    AnalysisMetrics,
    QCReport,
)

__all__ = [
    "NeuroTraceError",
    "InvalidFileFormatError",
    "CorruptedFileError",
    "InvalidDimensionsError",
    "MissingModalityError",
    "GeometryValidationError",
    "InferenceError",
    "VoxelSpacing",
    "ImageDimensions",
    "IntensityStats",
    "StudyMetadata",
    "ValidatedStudy",
    "PredictionMetadata",
    "SegmentationArtifact",
    "AnalysisMetrics",
    "QCReport",
]

