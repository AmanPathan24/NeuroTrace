"""NIfTI file loader and geometry validator for NeuroTrace."""
import os
import hashlib
import tempfile
import uuid
from pathlib import Path
from typing import Tuple, Union, BinaryIO, Optional
import numpy as np
import nibabel as nib
try:
    from nibabel.filebasedimages import ImageFileError
except ImportError:
    from nibabel.spatialimages import ImageFileError  # fallback for older nibabel

from core.contracts import (
    ValidatedStudy,
    StudyMetadata,
    ImageDimensions,
    VoxelSpacing,
    IntensityStats,
)
from core.errors import (
    InvalidFileFormatError,
    CorruptedFileError,
    InvalidDimensionsError,
    GeometryValidationError,
)


class NiftiLoader:
    """Robust loader and validator for brain MRI NIfTI volumes."""

    SUPPORTED_EXTENSIONS = (".nii", ".nii.gz")

    @classmethod
    def compute_sha256(cls, data: Union[bytes, Path, str]) -> str:
        """Compute SHA256 checksum for reproducibility tracking."""
        hasher = hashlib.sha256()
        if isinstance(data, bytes):
            hasher.update(data)
        else:
            with open(data, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def load_from_path(
        cls, file_path: Union[str, Path], study_id: Optional[str] = None
    ) -> Tuple[np.ndarray, nib.Nifti1Image, ValidatedStudy]:
        """
        Load and validate a NIfTI file from a local filesystem path.
        
        Args:
            file_path: Path to the .nii or .nii.gz file.
            study_id: Optional explicit study identifier. If None, generated.
            
        Returns:
            Tuple of (numpy 3D array, nibabel image object, ValidatedStudy schema).
        """
        path = Path(file_path)

        # Check extension first
        lower_name = path.name.lower()
        if not any(lower_name.endswith(ext) for ext in cls.SUPPORTED_EXTENSIONS):
            raise InvalidFileFormatError(
                f"Unsupported file format '{path.name}'. Only .nii and .nii.gz files are supported."
            )

        if not path.exists():
            raise CorruptedFileError(f"File not found: {path}")

        file_size = path.stat().st_size
        sha256_hash = cls.compute_sha256(path)

        try:
            nii_img = nib.load(str(path))
            raw_data = nii_img.get_fdata(dtype=np.float32)
        except (ImageFileError, OSError, EOFError) as e:
            raise CorruptedFileError(f"Failed to read NIfTI file: {e}") from e

        study_id = study_id or f"study_{uuid.uuid4().hex[:8]}"
        raw_data, validated_study = cls._validate_and_extract_metadata(
            raw_data=raw_data,
            nii_img=nii_img,
            filename=path.name,
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            study_id=study_id,
        )

        return raw_data, nii_img, validated_study

    @classmethod
    def load_from_bytes(
        cls, file_bytes: bytes, filename: str, study_id: Optional[str] = None
    ) -> Tuple[np.ndarray, nib.Nifti1Image, ValidatedStudy]:
        """
        Load and validate a NIfTI file from in-memory bytes (e.g. Streamlit upload).
        """
        import io
        import gzip

        lower_name = filename.lower()
        if not any(lower_name.endswith(ext) for ext in cls.SUPPORTED_EXTENSIONS):
            raise InvalidFileFormatError(
                f"Unsupported file format '{filename}'. Only .nii and .nii.gz files are supported."
            )

        file_size = len(file_bytes)
        sha256_hash = cls.compute_sha256(file_bytes)

        try:
            if lower_name.endswith(".nii.gz"):
                try:
                    decompressed = gzip.decompress(file_bytes)
                except gzip.BadGzipFile as e:
                    raise CorruptedFileError(f"Corrupted gzip compression: {e}") from e
                stream = io.BytesIO(decompressed)
            else:
                stream = io.BytesIO(file_bytes)

            nii_img = nib.Nifti1Image.from_stream(stream)
            raw_data = nii_img.get_fdata(dtype=np.float32)
        except (ImageFileError, OSError, EOFError, ValueError) as e:
            raise CorruptedFileError(f"Failed to parse uploaded NIfTI content: {e}") from e

        study_id = study_id or f"study_{uuid.uuid4().hex[:8]}"
        raw_data, validated_study = cls._validate_and_extract_metadata(
            raw_data=raw_data,
            nii_img=nii_img,
            filename=filename,
            file_size_bytes=file_size,
            sha256_hash=sha256_hash,
            study_id=study_id,
        )
        return raw_data, nii_img, validated_study

    @classmethod
    def _validate_and_extract_metadata(
        cls,
        raw_data: np.ndarray,
        nii_img: nib.Nifti1Image,
        filename: str,
        file_size_bytes: int,
        sha256_hash: str,
        study_id: str,
    ) -> Tuple[np.ndarray, ValidatedStudy]:
        """Internal validation and contract extraction pipeline."""
        validation_notes = []

        # 1. Dimension validation
        shape = raw_data.shape
        if len(shape) == 4 and shape[3] == 1:
            raw_data = np.squeeze(raw_data, axis=-1)
            validation_notes.append("Squeezed 4D singleton channel dimension to 3D.")
            shape = raw_data.shape

        if len(shape) != 3:
            raise InvalidDimensionsError(
                f"Expected 3D volume, but received {len(shape)}D array with shape {shape}."
            )

        dim_x, dim_y, dim_z = shape
        if dim_x < 32 or dim_y < 32 or dim_z < 16:
            raise InvalidDimensionsError(
                f"Volume dimensions {shape} are smaller than minimum acceptable MRI dimensions (32, 32, 16)."
            )

        # 2. Finite value and data integrity checks
        if not np.isfinite(raw_data).all():
            raise CorruptedFileError("Volume contains non-finite (NaN or Inf) voxel values.")

        min_val = float(raw_data.min())
        max_val = float(raw_data.max())
        mean_val = float(raw_data.mean())
        std_val = float(raw_data.std())

        if max_val <= min_val or std_val < 1e-4:
            raise CorruptedFileError(
                f"Volume contains flat/empty signal (min={min_val}, max={max_val}, std={std_val})."
            )

        # 3. Geometry and Voxel Spacing
        hdr = nii_img.header
        zooms = hdr.get_zooms()
        if len(zooms) < 3:
            raise GeometryValidationError(f"Incomplete voxel spacing zooms in header: {zooms}")

        dx, dy, dz = float(zooms[0]), float(zooms[1]), float(zooms[2])
        if dx <= 0 or dy <= 0 or dz <= 0:
            raise GeometryValidationError(
                f"Invalid non-positive voxel spacing: ({dx}, {dy}, {dz}) mm"
            )

        # 4. Affine and Orientation
        affine = nii_img.affine
        if affine is None or affine.shape != (4, 4):
            raise GeometryValidationError("Invalid or missing 4x4 spatial affine matrix in NIfTI header.")

        try:
            axcodes = nib.aff2axcodes(affine)
            orientation_str = "".join(axcodes)
        except Exception as e:
            orientation_str = "UNKNOWN"
            validation_notes.append(f"Failed to determine canonical orientation: {e}")

        # 5. Percentiles
        p01, p99 = np.percentile(raw_data, [1, 99])

        study = ValidatedStudy(
            metadata=StudyMetadata(
                study_id=study_id,
                filename=filename,
                file_size_bytes=file_size_bytes,
                sha256_hash=sha256_hash,
                modality="FLAIR",
            ),
            dimensions=ImageDimensions(dim_x=dim_x, dim_y=dim_y, dim_z=dim_z),
            spacing=VoxelSpacing(dx_mm=dx, dy_mm=dy, dz_mm=dz),
            orientation=orientation_str,
            affine_matrix=[[float(v) for v in row] for row in affine],
            intensity_stats=IntensityStats(
                min_value=min_val,
                max_value=max_val,
                mean_value=mean_val,
                std_value=std_val,
                p01_value=float(p01),
                p99_value=float(p99),
            ),
            is_valid=True,
            validation_notes=validation_notes,
        )
        return raw_data, study


def load_and_validate_mri(
    source: Union[str, Path, bytes], filename: Optional[str] = None, study_id: Optional[str] = None
) -> Tuple[np.ndarray, nib.Nifti1Image, ValidatedStudy]:
    """Convenience function to load and validate an MRI from path or bytes."""
    if isinstance(source, (str, Path)):
        return NiftiLoader.load_from_path(source, study_id=study_id)
    elif isinstance(source, bytes):
        if not filename:
            filename = "uploaded_mri.nii.gz"
        return NiftiLoader.load_from_bytes(source, filename=filename, study_id=study_id)
    else:
        raise InvalidFileFormatError(f"Unsupported source type: {type(source)}")

