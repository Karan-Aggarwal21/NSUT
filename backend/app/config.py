"""Cognivia – application configuration via pydantic-settings."""

from __future__ import annotations

import json
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_NAME: str = "Cognivia"
    APP_VERSION: str = "0.1.0"

    # Database: defaults to local SQLite so Docker is NOT required; override with PostgreSQL in .env if desired
    DATABASE_URL: str = "sqlite:///./cognivia.db"

    # JWT
    JWT_SECRET_KEY: str = "CHANGE-ME"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v):  # noqa: N805
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    # Image storage
    IMAGE_STORAGE_TYPE: str = "local"
    IMAGE_STORAGE_PATH: str = "./uploads/images"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000


settings = Settings()
