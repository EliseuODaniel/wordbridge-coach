"""Configuration settings for FillTheWord API"""

import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Project info
    PROJECT_NAME: str = "FillTheWord API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
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

settings = Settings()
