"""Configuration management using environment variables."""
import os
from pathlib import Path

# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")

    # Model Configuration
    MODEL_PATH: str = os.getenv(
        "MODEL_PATH", "models/codellama-7b-merged-Q4_K_M.gguf"
    )

    # Indexing Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "1048576"))  # 1MB
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # RAG Configuration
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    @classmethod
    def get_github_token(cls) -> Optional[str]:
        """Get GitHub token from environment."""
        return cls.GITHUB_TOKEN

    @classmethod
    def get_model_path(cls) -> Path:
        """Get model path as Path object."""
        model_path = os.getenv("MODEL_PATH", "models/codellama-7b-merged-Q4_K_M.gguf")
        full_path = BASE_DIR / model_path  # BASE_DIR = backend/
        return full_path


# Global settings instance
settings = Settings()
