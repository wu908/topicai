"""Shared FastAPI dependencies for the v2 API."""

from fastapi import HTTPException, Request


async def get_current_user(request: Request) -> dict:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录")

    user = await request.app.state.db.fetch_one(
        "SELECT id, email, username, ai_calls_today, created_at, last_login "
        "FROM users WHERE id = :id AND credentials_revoked_at IS NULL",
        {"id": user_id},
    )
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_db(request: Request):
    return request.app.state.db
