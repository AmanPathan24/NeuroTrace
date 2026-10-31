"""Inference adapter for NeuroSegNet 3D U-Net brain tumor segmentation."""
import os
import time
import uuid
import hashlib
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Union
import numpy as np
import torch

from config.settings import get_settings
from core.contracts import PredictionMetadata
from core.errors import InferenceError, CorruptedFileError
from imaging.preprocessor import normalize_flair, to_input_tensor
from models.unet3d import UNet3D


class NeuroSegNetAdapter:
    """
    Production-grade inference adapter for the verified 3D U-Net model.
    Preserves exact trained checkpoint weights and deterministic inference behavior.
    """

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
    ):
        settings = get_settings()
        self.checkpoint_path = Path(checkpoint_path or settings.default_checkpoint)
        
        # Resolve device
        if device is not None:
            self.device = device
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

        self.model: Optional[UNet3D] = None
        self.checkpoint_hash: Optional[str] = None
        self.epoch: Optional[int] = None
        self.val_loss: Optional[float] = None
        self.val_dice: Optional[list] = None

        self._load_checkpoint()

    def _compute_file_sha256(self, path: Path) -> str:
        """Compute SHA256 checksum of checkpoint file."""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _load_checkpoint(self) -> None:
        """Safely load and verify the PyTorch checkpoint weights."""
        if not self.checkpoint_path.exists():
            raise CorruptedFileError(
                f"Model checkpoint not found at: {self.checkpoint_path.resolve()}"
            )

        self.checkpoint_hash = self._compute_file_sha256(self.checkpoint_path)

        try:
            checkpoint = torch.load(
                self.checkpoint_path, map_location=self.device, weights_only=False
            )
        except Exception as e:
            raise CorruptedFileError(
                f"Failed to load PyTorch checkpoint from {self.checkpoint_path}: {e}"
            ) from e

        if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
            raise CorruptedFileError(
                f"Invalid checkpoint format. Expected dictionary with 'model_state_dict', got {type(checkpoint)}"
            )

        # Extract training metadata if present
        self.epoch = checkpoint.get("epoch")
        self.val_loss = checkpoint.get("val_loss")
        self.val_dice = checkpoint.get("val_dice")

        # Instantiate verified architecture: 1 input channel, 2 output classes, 8 base filters
        self.model = UNet3D(
            in_channels=1,
            out_channels=2,
            base_filters=8,
            dropout=0.2,
        ).to(self.device)

        # Strip DataParallel 'module.' prefix if present
        state_dict = checkpoint["model_state_dict"]
        clean_state_dict = OrderedDict()
        for k, v in state_dict.items():
            clean_key = k.replace("module.", "")
            clean_state_dict[clean_key] = v

        try:
            incompatible = self.model.load_state_dict(clean_state_dict, strict=True)
            if incompatible.missing_keys or incompatible.unexpected_keys:
                raise CorruptedFileError(
                    f"Checkpoint architecture mismatch! Missing: {incompatible.missing_keys}, Unexpected: {incompatible.unexpected_keys}"
                )
        except Exception as e:
            raise CorruptedFileError(f"Failed to load state dict into UNet3D: {e}") from e

        self.model.eval()

    def predict(
        self, raw_volume: np.ndarray, study_id: str = "study_unknown"
    ) -> Tuple[np.ndarray, PredictionMetadata]:
        """
        Execute deterministic brain tumor segmentation on an input 3D MRI volume.
        
        Args:
            raw_volume: 3D numpy array of FLAIR brain MRI.
            study_id: Study identifier for lineage tracking.
            
        Returns:
            Tuple of:
                - Binary segmentation mask (uint8 numpy array, shape matching raw_volume)
                - PredictionMetadata schema tracking execution metrics.
        """
        if self.model is None:
            raise InferenceError("Segmentation model is not loaded.")

        if raw_volume.ndim != 3:
            raise InferenceError(
                f"Model expects 3D volume (D, H, W), got {raw_volume.ndim}D array with shape {raw_volume.shape}"
            )

        try:
            # 1. Z-score volume normalization
            normalized = normalize_flair(raw_volume)

            # 2. Format 5D tensor: (1, 1, D, H, W)
            input_tensor = to_input_tensor(normalized, device=self.device)

            # 3. Deterministic inference without gradients
            start_time = time.perf_counter()
            with torch.no_grad():
                logits = self.model(input_tensor)
                pred_tensor = torch.argmax(logits, dim=1).squeeze()
                pred_mask = pred_tensor.cpu().numpy().astype(np.uint8)
            inference_duration = time.perf_counter() - start_time

            # 4. Create metadata
            prediction_id = f"pred_{uuid.uuid4().hex[:8]}"
            metadata = PredictionMetadata(
                prediction_id=prediction_id,
                study_id=study_id,
                model_name="NeuroSegNet 3D U-Net",
                checkpoint_file=self.checkpoint_path.name,
                checkpoint_hash=self.checkpoint_hash,
                device=self.device,
                inference_seconds=round(inference_duration, 3),
            )

            return pred_mask, metadata

        except Exception as e:
            raise InferenceError(f"Segmentation inference execution failed: {e}") from e

    def get_model_info(self) -> Dict[str, Any]:
        """Return technical summary of the loaded model and checkpoint."""
        if self.model is None:
            return {"status": "Not Loaded"}

        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

        return {
            "status": "Loaded",
            "architecture": "3D U-Net (4 levels, bottleneck, 4 upsample blocks)",
            "checkpoint_path": str(self.checkpoint_path),
            "checkpoint_sha256": self.checkpoint_hash,
            "epoch": self.epoch,
            "validation_loss": self.val_loss,
            "validation_dice": self.val_dice,
            "device": self.device,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "input_channels": 1,
            "output_channels": 2,
            "base_filters": 8,
        }

