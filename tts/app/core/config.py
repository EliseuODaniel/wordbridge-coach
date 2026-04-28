"""Configuration settings for the WordBridge Coach TTS service."""

from pydantic_settings import BaseSettings
from typing import Dict, Any


class Settings(BaseSettings):
    # Audio cache settings
    AUDIO_CACHE_PATH: str = "./audio"
    MODELS_PATH: str = "./models"
    
    # TTS settings
    DEFAULT_VOICE_ENGINE: str = "piper"
    SAMPLE_RATE: int = 22050
    MAX_TEXT_LENGTH: int = 500
    
    # Voice model configurations
    VOICE_MODELS: Dict[str, Dict[str, Any]] = {
        "en": {
            "code": "en",
            "name": "English",
            "piper_model": "lessac-glow_tts",
            "piper_voice": "lessac",
            "voice_type": "female",
            "language": "en"
        },
        "pt": {
            "code": "pt", 
            "name": "Português",
            "piper_model": "pt_br_female-glow_tts",
            "piper_voice": "pt_br_female",
            "voice_type": "female",
            "language": "pt-br"
        },
        "es": {
            "code": "es",
            "name": "Español",
            "piper_model": "es_male-glow_tts",
            "piper_voice": "es_male",
            "voice_type": "male",
            "language": "es"
        },
        "fr": {
            "code": "fr",
            "name": "Français",
            "piper_model": "fr_female-glow_tts",
            "piper_voice": "fr_female",
            "voice_type": "female",
            "language": "fr"
        }
    }
    
    # Cache settings
    CACHE_HIT_RESPONSE_TIME_MS: int = 20
    CACHE_MISS_MAX_TIME_MS: int = 1500
    
    # Supported languages
    SUPPORTED_LANGUAGES: list = list(VOICE_MODELS.keys())
    
    class Config:
        env_file = ".env"


settings = Settings()
