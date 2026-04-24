"""WordBridge Coach API - Main FastAPI application."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.api_v1.api import api_router
from app.core.config import ensure_runtime_safety, settings, collect_runtime_issues


logger = logging.getLogger(__name__)


def run_startup_checks() -> None:
    """Run lightweight startup configuration checks."""
    if settings.DEBUG:
        for issue in collect_runtime_issues():
            logger.warning("Configuration warning: %s", issue)
        return

    ensure_runtime_safety()
    for issue in collect_runtime_issues():
        logger.warning("Configuration warning: %s", issue)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown checks."""
    run_startup_checks()
    logger.info("WordBridge Coach API started")
    yield
    logger.info("WordBridge Coach API stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="WordBridge Coach - Local vocabulary training across cards, cloze and chat coaching",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "WordBridge Coach API"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "WordBridge Coach API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
