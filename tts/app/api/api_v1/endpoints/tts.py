"""TTS endpoints for WordBridge Coach."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Response, Query, Path
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging

from app.services.tts_service import get_tts_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class TTSRequest(BaseModel):
    """Request model for TTS generation"""
    text: str
    lang: str
    voice_type: Optional[str] = "female"
    kind: Optional[str] = "word"  # word or sentence


@router.get("/word/{word_id}")
async def get_word_audio(
    word_id: str,
    text: str = Query(..., description="Word text to convert to speech"),
    lang: str = Query("en", description="Language code"),
):
    """
    Get audio for a word
    Generates or returns cached audio file
    """
    try:
        if lang not in settings.SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {lang}. Supported: {settings.SUPPORTED_LANGUAGES}"
            )
        
        # Validate text length
        if len(text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Max length: {settings.MAX_TEXT_LENGTH}"
            )
        
        # Get TTS service
        tts_service = get_tts_service()
        
        # Generate or get cached audio
        audio_data = await tts_service.generate_audio(text, lang, "word")
        
        if audio_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate audio"
            )
        
        # Return audio file
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/wav",
            headers={
                "Content-Length": str(len(audio_data)),
                "X-Cache": "HIT" if tts_service.get_audio_url(text, lang, "word") else "MISS",
                "X-Language": lang,
                "X-Type": "word"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating word audio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sentence/{sentence_id}")
async def get_sentence_audio(
    sentence_id: str,
    text: str = Query(..., description="Sentence text to convert to speech"),
    lang: str = Query("en", description="Language code"),
):
    """
    Get audio for a sentence
    Generates or returns cached audio file
    """
    try:
        if lang not in settings.SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {lang}. Supported: {settings.SUPPORTED_LANGUAGES}"
            )
        
        # Validate text length
        if len(text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Max length: {settings.MAX_TEXT_LENGTH}"
            )
        
        # Get TTS service
        tts_service = get_tts_service()
        
        # Generate or get cached audio
        audio_data = await tts_service.generate_audio(text, lang, "sentence")
        
        if audio_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate audio"
            )
        
        # Return audio file
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/wav",
            headers={
                "Content-Length": str(len(audio_data)),
                "X-Cache": "HIT" if tts_service.get_audio_url(text, lang, "sentence") else "MISS",
                "X-Language": lang,
                "X-Type": "sentence"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating sentence audio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate")
async def generate_audio(request: TTSRequest):
    """
    Generate audio directly via POST (alternative to GET endpoints)
    """
    try:
        if request.lang not in settings.SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language: {request.lang}"
            )
        
        if len(request.text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Max length: {settings.MAX_TEXT_LENGTH}"
            )
        
        # Get TTS service
        tts_service = get_tts_service()
        
        # Generate audio
        audio_data = await tts_service.generate_audio(
            request.text, 
            request.lang, 
            request.kind
        )
        
        if audio_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate audio"
            )
        
        # Return audio file
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/wav",
            headers={
                "Content-Length": str(len(audio_data)),
                "X-Cache": "MISS",  # Always miss for direct generation
                "X-Generated": "true"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/audio/{lang}/{audio_type}/{slug}.wav")
async def get_cached_audio(
    lang: str = Path(..., description="Language code"),
    audio_type: str = Path(..., description="Audio type (word/sentence)"),
    slug: str = Path(..., description="Audio file slug"),
):
    """
    Serve static cached audio files
    """
    try:
        if lang not in settings.SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=404, detail="Language not supported")
        
        if audio_type not in ["word", "sentence"]:
            raise HTTPException(status_code=404, detail="Invalid audio type")
        
        # Construct file path
        from pathlib import Path
        audio_path = Path(settings.AUDIO_CACHE_PATH) / lang / audio_type / f"{slug}.wav"
        
        if not audio_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Audio not found"
            )
        
        # Return static file
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
                "X-Cache": "HIT"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving cached audio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/cache")
async def clear_cache(
    lang: Optional[str] = Query(None, description="Language code to clear"),
    audio_type: Optional[str] = Query(None, description="Audio type to clear")
):
    """
    Clear audio cache
    """
    try:
        tts_service = get_tts_service()
        tts_service.clear_cache(lang, audio_type)
        
        return {"message": "Cache cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check for TTS service"""
    try:
        tts_service = get_tts_service()
        return {
            "status": "healthy",
            "service": "WordBridge Coach TTS Service",
            "cache_path": settings.AUDIO_CACHE_PATH,
            "supported_languages": settings.SUPPORTED_LANGUAGES
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")
