"""Inference adapter for NeuroSegNet 3D U-Net brain tumor segmentation."""
import os
import gc
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
        """
        Load trained weights from checkpoint using strict state_dict verification.
        Handles DataParallel 'module.' prefix stripping if present.
        """
        if not self.checkpoint_path.exists():
            raise CorruptedFileError(
                f"Checkpoint file '{self.checkpoint_path}' does not exist."
            )

        self.checkpoint_hash = self._compute_file_sha256(self.checkpoint_path)

        try:
            checkpoint = torch.load(
                self.checkpoint_path,
                map_location=self.device,
                weights_only=False,
            )
        except Exception as e:
            raise CorruptedFileError(
                f"Failed to load PyTorch checkpoint from {self.checkpoint_path}: {e}"
            ) from e

        # Extract training metadata if present
        if isinstance(checkpoint, dict):
            self.epoch = checkpoint.get("epoch")
            self.val_loss = checkpoint.get("val_loss")
            self.val_dice = checkpoint.get("val_dice")
            state_dict = checkpoint.get("model_state_dict", checkpoint)
        else:
            state_dict = checkpoint

        # Strip DataParallel 'module.' prefix if present
        cleaned_state_dict = OrderedDict()
        for k, v in state_dict.items():
            name = k[7:] if k.startswith("module.") else k
            cleaned_state_dict[name] = v

        # Instantiate verified architecture: 1 input channel, 2 output classes, 8 base filters
        self.model = UNet3D(
            in_channels=1,
            out_channels=2,
            base_filters=8,
            dropout=0.2,
        )

        try:
            missing_keys, unexpected_keys = self.model.load_state_dict(
                cleaned_state_dict, strict=True
            )
            if missing_keys or unexpected_keys:
                raise CorruptedFileError(
                    f"Checkpoint key mismatch: missing={missing_keys}, unexpected={unexpected_keys}"
                )
        except Exception as e:
            raise CorruptedFileError(
                f"Strict state_dict loading failed for {self.checkpoint_path}: {e}"
            ) from e

        self.model.to(self.device)
        self.model.eval()

    def predict(
        self,
        raw_volume: np.ndarray,
        study_id: str = "unknown_study",
    ) -> Tuple[np.ndarray, PredictionMetadata]:
        """
        Execute deterministic 3D segmentation inference on a raw brain MRI volume.
        
        Args:
            raw_volume: 3D numpy array of raw FLAIR intensities (D, H, W).
            study_id: Identifier of the study for provenance tracking.
            
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

            # Clean up intermediate memory aggressively
            del logits, pred_tensor, input_tensor, normalized
            gc.collect()

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
