"""API v1 router for FillTheWord"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import cards, stats, settings

api_router = APIRouter()

# Include cards endpoints
api_router.include_router(
    cards.router,
    prefix="/cards",
    tags=["cards"]
)

# Include stats endpoints
api_router.include_router(
    stats.router,
    prefix="/stats",
    tags=["stats"]
)

# Include settings endpoints
api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"]
)
