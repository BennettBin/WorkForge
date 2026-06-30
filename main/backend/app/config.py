import os
from pathlib import Path

from pydantic import BaseModel, Field


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if raw is None:
        return default
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    return values or default


def _env_path(name: str, default: Path) -> Path:
    raw = (os.getenv(name) or "").strip()
    return Path(raw) if raw else default


class Settings(BaseModel):
    app_name: str = Field(default_factory=lambda: os.getenv("WORKFORGE_APP_NAME", "WorkForge"))
    app_env: str = Field(default_factory=lambda: os.getenv("WORKFORGE_APP_ENV", "development"))
    app_version: str = Field(default_factory=lambda: os.getenv("WORKFORGE_APP_VERSION", "0.1.0"))
    host: str = Field(default_factory=lambda: os.getenv("WORKFORGE_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: _env_int("WORKFORGE_PORT", 8080))
    data_dir: Path = Field(
        default_factory=lambda: _env_path(
            "WORKFORGE_DATA_DIR",
            Path(__file__).resolve().parents[2] / "runtime_data" / "storage",
        )
    )
    max_upload_size_bytes: int = Field(
        default_factory=lambda: _env_int("WORKFORGE_MAX_UPLOAD_SIZE_BYTES", 50 * 1024 * 1024)
    )
    default_task_timeout_seconds: int = Field(
        default_factory=lambda: _env_int("WORKFORGE_TASK_TIMEOUT_SECONDS", 15 * 60)
    )
    active_user_window_seconds: int = Field(
        default_factory=lambda: _env_int("WORKFORGE_ACTIVE_USER_WINDOW_SECONDS", 600)
    )
    cors_origins: tuple[str, ...] = Field(
        default_factory=lambda: _env_list(
            "WORKFORGE_CORS_ORIGINS",
            ("http://127.0.0.1:8080", "http://localhost:8080"),
        )
    )
    admin_email: str = Field(default_factory=lambda: os.getenv("WORKFORGE_ADMIN_EMAIL", "admin"))
    admin_username: str = Field(default_factory=lambda: os.getenv("WORKFORGE_ADMIN_USERNAME", "admin"))
    admin_password: str = Field(default_factory=lambda: os.getenv("WORKFORGE_ADMIN_PASSWORD", "123456"))
    log_level: str = Field(default_factory=lambda: os.getenv("WORKFORGE_LOG_LEVEL", "INFO"))


settings = Settings()
