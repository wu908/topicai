"""FastAPI dependencies for TopicAI v4.0.

Provides reusable Depends() callables for authentication, database access,
and other cross-cutting concerns.
"""

from fastapi import HTTPException, Request


async def get_current_user(request: Request) -> dict:
    """Dependency that extracts and validates the current authenticated user.

    Relies on request.state.user_id set by JWTAuthMiddleware.
    Returns the user dict or raises 401.

    Usage:
        @router.get("/me")
        async def me(user: dict = Depends(get_current_user)):
            return {"user": user}
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    db = request.app.state.db
    user = await db.fetch_one(
        "SELECT id, email, username, ai_calls_today, created_at, last_login "
        "FROM users WHERE id = :id",
        {"id": user_id},
    )
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


def get_db(request: Request):
    """Dependency that returns the shared Database instance from app state."""
    return request.app.state.db
