from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = ",".join(
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
    ]
)


def normalize_database_url(raw_url: str) -> str:
    normalized = raw_url.strip()
    if normalized.startswith("postgres://"):
        return "postgresql+psycopg://" + normalized[len("postgres://") :]
    if normalized.startswith("postgresql://") and "+psycopg" not in normalized:
        return "postgresql+psycopg://" + normalized[len("postgresql://") :]
    return normalized


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="AU Esports Platform API", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(default="sqlite:///./dev.db", alias="DATABASE_URL")
    auto_create_tables: bool = Field(default=False, alias="AUTO_CREATE_TABLES")

    cors_origins: str = Field(default=DEFAULT_CORS_ORIGINS, alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    enable_debug_routes: bool = Field(default=False, alias="ENABLE_DEBUG_ROUTES")

    uploads_root: str = Field(default="", alias="UPLOADS_ROOT")
    media_backend: str = Field(default="local", alias="MEDIA_BACKEND")
    media_azure_blob_connection_string: str | None = Field(
        default=None,
        alias="MEDIA_AZURE_BLOB_CONNECTION_STRING",
    )
    media_azure_blob_container: str = Field(
        default="au-esports-media",
        alias="MEDIA_AZURE_BLOB_CONTAINER",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("DATABASE_URL must be a non-empty string")
        return normalize_database_url(value)

    @field_validator("media_backend", mode="before")
    @classmethod
    def _normalize_media_backend(cls, value: str) -> str:
        normalized = str(value or "local").strip().lower()
        if normalized not in {"local", "azure_blob"}:
            raise ValueError("MEDIA_BACKEND must be either 'local' or 'azure_blob'")
        return normalized

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() in {"production", "prod"}

    @property
    def uploads_root_path(self) -> Path:
        configured = self.uploads_root.strip()
        if configured:
            return Path(configured).expanduser().resolve()
        return (Path(__file__).resolve().parents[2] / "uploads").resolve()

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
