"""API v1 router for the WordBridge Coach TTS service."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import tts

api_router = APIRouter()

# Include TTS endpoints
api_router.include_router(
    tts.router, 
    prefix="/tts", 
    tags=["tts"]
)
