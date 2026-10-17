"""V1 API router combining all endpoint modules."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    cognitive,
    history,
    personalized,
    profiles,
    questionnaires,
    settings,
    sync,
    users,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(profiles.router)
api_router.include_router(cognitive.router)
api_router.include_router(personalized.router)
api_router.include_router(questionnaires.router)
api_router.include_router(history.router)
api_router.include_router(sync.router)
api_router.include_router(settings.router)
api_router.include_router(admin.router)
