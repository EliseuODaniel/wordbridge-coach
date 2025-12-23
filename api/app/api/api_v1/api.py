"""API v1 router for FillTheWord"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import cards, stats, settings, users
from app.api.api_v1.endpoints.analytics import insights

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

# Include users endpoints
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# Include insights endpoints
api_router.include_router(
    insights.router,
    prefix="/insights",
    tags=["insights"]
)
