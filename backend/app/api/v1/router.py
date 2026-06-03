"""API v1 main router.

Aggregates all v1 sub-routers and registers them under /api/v1.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.health import router as health_router
from app.api.v1.ideas import router as ideas_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.publish import router as publish_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.titles import router as titles_router
from app.api.v1.topics import router as topics_router
from app.api.v1.tracks import router as tracks_router
from app.api.v1.viral import router as viral_router

api_v1_router = APIRouter()

# Health endpoints (no auth required)
api_v1_router.include_router(health_router, tags=["Health"])

# Auth endpoints (registration, login, token refresh)
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Profiles endpoints (onboarding, profile CRUD)
api_v1_router.include_router(profiles_router, tags=["Profiles"])

# Feedback endpoints (submit, analysis)
api_v1_router.include_router(feedback_router, tags=["Feedback"])

# Topics endpoints (recommend, refresh, explain)
api_v1_router.include_router(topics_router, tags=["Topics"])

# Viral analysis endpoints (analyze, result)
api_v1_router.include_router(viral_router, tags=["Viral"])

# Ideas endpoints (boost)
api_v1_router.include_router(ideas_router, tags=["Ideas"])

# Titles endpoints (optimize)
api_v1_router.include_router(titles_router, tags=["Titles"])

# Tracks endpoints (diagnose)
api_v1_router.include_router(tracks_router, tags=["Tracks"])

# Publish advisor endpoints (suggest)
api_v1_router.include_router(publish_router, tags=["Publish"])

# Reviews endpoints (predict, attribute)
api_v1_router.include_router(reviews_router, tags=["Reviews"])
