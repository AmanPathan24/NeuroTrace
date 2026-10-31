"""Global settings and configuration management for NeuroTrace."""
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

# Base directory is the workspace root
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    """Application configuration schema."""
    
    # Project Info
    app_name: str = "NeuroTrace"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False)
    
    # Storage Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = Field(default=BASE_DIR / "data")
    checkpoints_dir: Path = Field(default=BASE_DIR / "Flairbased_2")
    default_checkpoint: Path = Field(default=BASE_DIR / "Flairbased_2" / "model_epoch_45 (1).pt")
    
    # Compute Device
    device: str = Field(default="cpu")
    
    # Model Architecture Config
    in_channels: int = 1
    out_channels: int = 2
    base_filters: int = 8
    dropout: float = 0.2
    
    # Supported Modalities
    supported_modalities: list[str] = Field(default_factory=lambda: ["flair"])
    
    # Gemma 4 / Gemini API Config
    gemini_api_key: Optional[str] = Field(default=None)
    gemma_model_id: str = Field(default="gemini-2.5-flash")
    
    # Streamlit Config
    server_port: int = 8501
    
    model_config = {
        "arbitrary_types_allowed": True
    }

    @classmethod
    def load_from_env(cls) -> "Settings":
        """Instantiate Settings reading from environment variables with fallback defaults."""
        device = os.getenv("NEUROTRACE_DEVICE", "cpu")
        model_path_env = os.getenv("NEUROTRACE_MODEL_PATH")
        checkpoint_path = Path(model_path_env) if model_path_env else (BASE_DIR / "Flairbased_2" / "model_epoch_45 (1).pt")
        if not checkpoint_path.is_absolute():
            checkpoint_path = BASE_DIR / checkpoint_path
            
        data_dir_env = os.getenv("NEUROTRACE_DATA_DIR")
        data_path = Path(data_dir_env) if data_dir_env else (BASE_DIR / "data")
        if not data_path.is_absolute():
            data_path = BASE_DIR / data_path
            
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")
        gemma_model = os.getenv("GEMMA_MODEL_ID", "gemini-2.5-flash")
        
        return cls(
            default_checkpoint=checkpoint_path,
            data_dir=data_path,
            device=device,
            gemini_api_key=api_key,
            gemma_model_id=gemma_model
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton instance of Settings."""
    return Settings.load_from_env()

