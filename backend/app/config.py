"""Application configuration from environment."""
import os
from pathlib import Path

from pydantic_settings import BaseSettings

# Prefer .env in backend/ or project root (parent of backend)
_backend_dir = Path(__file__).resolve().parent.parent
_env_files = [_backend_dir / ".env", _backend_dir.parent / ".env"]


class Settings(BaseSettings):
    openai_api_key: str = ""
    chroma_persist_dir: str = "./data/chroma"
    data_dir: str = "./data"

    class Config:
        env_file = next((str(p) for p in _env_files if p.exists()), ".env")
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", "./data/chroma"),
        data_dir=os.getenv("DATA_DIR", "./data"),
    )


def ensure_dirs(settings: Settings) -> None:
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
