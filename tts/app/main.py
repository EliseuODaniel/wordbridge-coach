"""FillTheWord TTS Service - Main FastAPI Application"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.api.api_v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="FillTheWord TTS Service",
    version="0.1.0",
    description="Text-to-Speech service for FillTheWord vocabulary learning",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for TTS service
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# Ensure audio cache directory exists
os.makedirs(settings.AUDIO_CACHE_PATH, exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FillTheWord TTS Service"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FillTheWord TTS Service",
        "version": "0.1.0",
        "endpoints": ["/api/tts/word", "/api/tts/sentence", "/api/audio"]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
