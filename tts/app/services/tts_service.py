"""TTS service implementation for WordBridge Coach."""

import os
import hashlib
import asyncio
import subprocess
import tempfile
from typing import Optional, BinaryIO
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

import soundfile as sf
import numpy as np


class TTSService:
    """TTS Service with caching and multiple engine support"""
    
    def __init__(self, cache_path: str, models_path: str):
        self.cache_path = Path(cache_path)
        self.models_path = Path(models_path)
        self.voices = {}
        self.piper_available = self._check_piper_availability()

        # Ensure directories exist
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.models_path.mkdir(parents=True, exist_ok=True)

        # Initialize voice models
        self._initialize_voices()

    def _check_piper_availability(self) -> bool:
        """Check if Piper CLI is available"""
        try:
            result = subprocess.run(['piper', '--help'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Piper CLI is available")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Piper CLI not available: {e}")
        return False

    def _initialize_voices(self):
        """Initialize TTS voice models"""
        if not self.piper_available:
            logger.error("❌ Piper CLI not available - please run download script")
            return

        # Check for model files
        languages = ['en', 'es', 'fr', 'pt']
        self.voices = {}

        for lang in languages:
            model_path = self.models_path / lang / 'model.onnx'
            config_path = self.models_path / lang / 'model.onnx.json'

            if model_path.exists() and config_path.exists():
                self.voices[lang] = {
                    'model': str(model_path),
                    'config': str(config_path)
                }
                logger.info(f"✅ Found {lang} model: {model_path}")
            else:
                logger.warning(f"❌ Missing {lang} model files")

        if self.voices:
            logger.info(f"🎵 TTS Service initialized with {len(self.voices)} voice models")
        else:
            logger.error("❌ No voice models found - please run download script")
    
    def _get_cache_path(self, text: str, language: str, audio_type: str) -> Path:
        """Generate cache file path for audio"""
        # Create slug from text to avoid filesystem issues
        text_slug = hashlib.md5(text.encode()).hexdigest()[:12]
        filename = f"{text_slug}.wav"
        
        # Create language/type subdirectory
        lang_dir = self.cache_path / language / audio_type
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        return lang_dir / filename
    
    async def generate_audio(
        self,
        text: str,
        language: str,
        audio_type: str = "word"
    ) -> Optional[bytes]:
        """
        Generate audio for given text and language using Piper TTS

        Args:
            text: Text to convert to speech
            language: Language code (en, pt, es, fr)
            audio_type: Type of audio (word, sentence)

        Returns:
            Audio data as bytes or None if failed
        """
        try:
            # Check cache first
            cache_path = self._get_cache_path(text, language, audio_type)
            if cache_path.exists():
                logger.info(f"Cache hit: {cache_path}")
                return cache_path.read_bytes()

            # Check if we have a voice model for this language
            if language not in self.voices:
                logger.error(f"No voice model available for language: {language}")
                # Fallback to English if available
                if 'en' in self.voices:
                    logger.info(f"Falling back to English voice for: {language}")
                    language = 'en'
                else:
                    logger.error("No voice models available at all")
                    return None

            # Generate audio if not in cache
            logger.info(f"Cache miss: Generating audio for '{text}' in {language}")

            audio_data = await self._generate_piper_audio(text, language)

            # Save to cache
            if audio_data:
                cache_path.write_bytes(audio_data)
                logger.info(f"Saved audio to cache: {cache_path}")

            return audio_data

        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None
    
    async def _generate_piper_audio(self, text: str, language: str) -> Optional[bytes]:
        """
        Generate audio using Piper TTS CLI
        """
        if language not in self.voices:
            logger.error(f"No voice model for language: {language}")
            return None

        voice_config = self.voices[language]

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
            audio_file_path = audio_file.name

        try:
            # Run Piper CLI with text from stdin
            cmd = [
                'piper',
                '--model', voice_config['model'],
                '-c', voice_config['config'],
                '-f', audio_file_path
            ]

            logger.info(f"Running Piper: {' '.join(cmd)} with text '{text}'")

            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    input=text,  # Pass text via stdin
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout
                )
            )

            if result.returncode != 0:
                logger.error(f"Piper CLI failed: {result.stderr}")
                return None

            # Read generated audio file
            if os.path.exists(audio_file_path):
                with open(audio_file_path, 'rb') as f:
                    audio_data = f.read()

                # Log success with file size
                logger.info(f"Generated {len(audio_data)} bytes of audio for '{text}'")
                return audio_data
            else:
                logger.error("Piper CLI completed but no output file found")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Piper CLI timed out")
            return None
        except Exception as e:
            logger.error(f"Error running Piper CLI: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(audio_file_path):
                    os.unlink(audio_file_path)
            except OSError:
                pass
    
    def get_audio_url(self, text: str, language: str, audio_type: str) -> str:
        """
        Get URL for cached audio file
        
        Args:
            text: Text that was converted to speech
            language: Language code
            audio_type: Type of audio (word, sentence)
            
        Returns:
            URL path for the audio file
        """
        cache_path = self._get_cache_path(text, language, audio_type)
        if cache_path.exists():
            text_slug = cache_path.stem
            return f"/api/audio/{language}/{audio_type}/{text_slug}.wav"
        return ""
    
    def clear_cache(self, language: Optional[str] = None, audio_type: Optional[str] = None):
        """Clear audio cache"""
        try:
            if language and audio_type:
                # Clear specific language/type
                cache_dir = self.cache_path / language / audio_type
                if cache_dir.exists():
                    for file in cache_dir.glob("*.wav"):
                        file.unlink()
            elif language:
                # Clear entire language
                lang_dir = self.cache_path / language
                if lang_dir.exists():
                    for audio_dir in lang_dir.iterdir():
                        if audio_dir.is_dir():
                            for file in audio_dir.glob("*.wav"):
                                file.unlink()
            else:
                # Clear all cache
                for lang_dir in self.cache_path.iterdir():
                    if lang_dir.is_dir():
                        for audio_dir in lang_dir.iterdir():
                            if audio_dir.is_dir():
                                for file in audio_dir.glob("*.wav"):
                                    file.unlink()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


# Global TTS service instance
tts_service = None


def get_tts_service() -> TTSService:
    """Get global TTS service instance"""
    global tts_service
    if tts_service is None:
        from app.core.config import settings
        tts_service = TTSService(
            cache_path=settings.AUDIO_CACHE_PATH,
            models_path=settings.MODELS_PATH
        )
    return tts_service
