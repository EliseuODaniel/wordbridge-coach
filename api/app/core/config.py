"""Configuration settings for WordBridge Coach API."""

from __future__ import annotations

import logging
import os
from typing import List, Union

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)

_PLACEHOLDER_SECRETS = {
    "your-secret-key-change-in-production",
    "your-secret-key-change-in-production-please",
    "change-me",
    "changeme",
    "secret",
    "test-secret",
    "",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Project info
    PROJECT_NAME: str = "WordBridge Coach API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    STRICT_CONFIG: bool = False
    
    # Security
    SECRET_KEY: str = Field(default="")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./filltheword.db")
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3007", "http://127.0.0.1:3007"]
    
    # TTS Service
    TTS_SERVICE_URL: str = "http://localhost:8001"
    AUDIO_CACHE_PATH: str = "./audio"
    
    # SRS Settings
    DEFAULT_EASINESS_FACTOR: float = 2.5
    MIN_EASINESS_FACTOR: float = 1.3
    MAX_EASINESS_FACTOR: float = 2.5
    DEFAULT_NEW_CARDS_PER_DAY: int = 10
    MAX_NEW_CARDS_PER_DAY: int = 50
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @model_validator(mode="after")
    def _validate_runtime_invariants(self) -> "Settings":
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set")
        if not self.ALLOWED_HOSTS:
            raise ValueError("ALLOWED_HOSTS must contain at least one allowed origin")
        self.SECRET_KEY = self.SECRET_KEY.strip()
        return self


def collect_runtime_issues() -> list[str]:
    """Return runtime configuration issues that should be reviewed before serving traffic."""
    issues = []
    normalized_secret = settings.SECRET_KEY.strip()
    normalized_env = settings.ENVIRONMENT.lower().strip()
    if not normalized_secret:
        issues.append("SECRET_KEY is empty; JWT sessions cannot be used safely.")
    elif normalized_secret.lower() in _PLACEHOLDER_SECRETS:
        issues.append(
            f"SECRET_KEY uses placeholder value '{normalized_secret}'. "
            "Replace with a generated secret in non-local environments."
        )

    if not settings.DEBUG and normalized_env in {"production", "prod"} and issues:
        issues.append("Production-like environment is running with DEBUG=false but insecure secrets.")

    return issues


def ensure_runtime_safety() -> list[str]:
    """Validate runtime safety and return blocking issues under strict mode."""
    issues = collect_runtime_issues()
    if settings.STRICT_CONFIG and issues:
        raise RuntimeError(
            "Strict runtime validation failed: " + "; ".join(issues)
        )
    return issues


settings = Settings()
