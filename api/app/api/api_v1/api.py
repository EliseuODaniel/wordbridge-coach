"""API v1 router for WordBridge Coach."""

from fastapi import APIRouter

from app.api.api_v1.endpoints import cards, stats, settings, users, chat, llm_profiles
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

# Include chat endpoints (Chat Coach mode)
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

# Include LLM profile endpoints
api_router.include_router(
    llm_profiles.router,
    tags=["llm-profiles"]
)
