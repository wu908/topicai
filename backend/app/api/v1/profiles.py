"""Profiles API endpoints for TopicAI v4.0.

Provides onboarding submission, profile retrieval, and profile updates.
Requires JWT authentication.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.v1.deps import get_current_user
from app.models.creator_profile import OnboardingRequest, ProfileUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Profiles"])

@router.post("/profiles/onboarding", status_code=201)
async def submit_onboarding(
    request: Request,
    data: OnboardingRequest,
    user: dict = Depends(get_current_user),
):
    """Submit onboarding answers and generate a creator profile.

    Idempotent: re-submitting onboarding updates the existing profile
    rather than raising a UNIQUE(user_id) violation.

    Args:
        request: FastAPI request object.
        data: Onboarding answers (track, content_formats, etc.).
        user: Authenticated user (injected by Depends via JWT middleware).

    Returns:
        Created CreatorProfile with 201 status.
    """
    from app.services.creator_profile import CreatorProfileService
    from app.services.onboarding import OnboardingService

    user_id = user["id"]
    db = request.app.state.db
    onboarding_svc = OnboardingService()
    profile_svc = CreatorProfileService(db)

    try:
        profile = onboarding_svc.generate_profile(user_id, data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    # Persist (upsert) so GET /profiles/me can find it. Re-onboarding
    # replaces profile fields while keeping id / user_id / created_at.
    profile_dict = profile.model_dump()
    if await profile_svc.exists(user_id):
        updates = {
            k: v for k, v in profile_dict.items()
            if k not in {"id", "user_id", "created_at"}
        }
        await profile_svc.update(user_id, updates)
    else:
        await profile_svc.create(profile_dict)

    return {
        "code": 201,
        "data": {
            "id": profile.id,
            "user_id": profile.user_id,
            "track": profile.track,
            "content_formats": profile.content_formats,
            "production_complexity": profile.production_complexity,
            "content_depth": profile.content_depth,
            "hotspot_preference": profile.hotspot_preference,
            "recommendation_mode": profile.recommendation_mode,
            "rubric_weights": profile.rubric_weights,
            "created_at": profile.created_at,
        },
        "message": "创作画像创建成功",
        "meta": {},
    }

@router.get("/profiles/me")
async def get_my_profile(request: Request, user: dict = Depends(get_current_user)):
    """Get the current user's creator profile.

    Args:
        request: FastAPI request object.
        user: Current authenticated user (injected by Depends).

    Returns:
        User's CreatorProfile or 404 if not found.
    """
    from app.services.creator_profile import CreatorProfileService

    db = request.app.state.db
    svc = CreatorProfileService(db)
    profile = await svc.get(user["id"])

    if not profile:
        raise HTTPException(status_code=404, detail="尚未创建创作画像，请先完成Onboarding")

    return {
        "code": 200,
        "data": {
            "id": profile["id"],
            "user_id": profile["user_id"],
            "track": profile["track"],
            "content_formats": profile["content_formats"],
            "production_complexity": profile["production_complexity"],
            "content_depth": profile["content_depth"],
            "hotspot_preference": profile["hotspot_preference"],
            "recommendation_mode": profile["recommendation_mode"],
            "rubric_weights": profile["rubric_weights"],
            "created_at": profile["created_at"],
            "updated_at": profile["updated_at"],
        },
        "message": "success",
        "meta": {},
    }

@router.put("/profiles/me")
async def update_my_profile(request: Request, data: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    """Update the current user's creator profile.

    Args:
        request: FastAPI request object.
        data: Fields to update.
        user: Current authenticated user (injected by Depends).

    Returns:
        Updated profile confirmation.
    """
    from app.services.creator_profile import CreatorProfileService

    db = request.app.state.db
    svc = CreatorProfileService(db)
    exists = await svc.exists(user["id"])
    if not exists:
        raise HTTPException(status_code=404, detail="尚未创建创作画像")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        await svc.update(user["id"], updates)

    return {
        "code": 200,
        "data": None,
        "message": "创作画像更新成功",
        "meta": {},
    }
