"""Custom exception hierarchy for NeuroTrace."""

class NeuroTraceError(Exception):
    """Base exception for all NeuroTrace errors."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class InvalidFileFormatError(NeuroTraceError):
    """Raised when an uploaded or specified file has an unsupported format or extension."""
    pass


class CorruptedFileError(NeuroTraceError):
    """Raised when an MRI file cannot be read, parsed, or contains unreadable byte content."""
    pass


class InvalidDimensionsError(NeuroTraceError):
    """Raised when an MRI volume does not have the expected 3D spatial dimensions."""
    pass


class MissingModalityError(NeuroTraceError):
    """Raised when a required MRI sequence/modality (e.g. FLAIR) is missing."""
    pass


class GeometryValidationError(NeuroTraceError):
    """Raised when an MRI affine, voxel spacing, or spatial orientation fails validation."""
    pass


class InferenceError(NeuroTraceError):
    """Raised when model inference fails during preprocessing, forward pass, or postprocessing."""
    pass

