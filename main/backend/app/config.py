from pathlib import Path
from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = "WorkForge"
    app_env: str = "development"
    app_version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 8080
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "storage")
    max_upload_size_bytes: int = 50 * 1024 * 1024
    default_task_timeout_seconds: int = 15 * 60


settings = Settings()
