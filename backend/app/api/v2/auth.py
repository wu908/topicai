"""Authentication endpoints for the v2-only API."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import get_current_user
from app.models.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=ApiResponse, status_code=201)
async def register(req: Request, body: RegisterRequest):
    from app.core.auth import AuthManager
    from app.core.exceptions import UserAlreadyExistsException

    try:
        user, tokens = await AuthManager(db=req.app.state.db).register(
            email=body.email,
            username=body.username,
            password=body.password,
        )
    except UserAlreadyExistsException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return {
        "code": 201,
        "data": {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "ai_calls_today": user.get("ai_calls_today", 0),
                "last_login": user.get("last_login"),
                "created_at": user["created_at"],
            },
            **tokens,
            "token_type": "bearer",
        },
        "message": "注册成功",
        "meta": {},
    }


@router.post("/login", response_model=ApiResponse)
async def login(req: Request, body: LoginRequest):
    from app.core.auth import AuthManager
    from app.core.exceptions import AuthenticationException

    try:
        user, tokens = await AuthManager(db=req.app.state.db).login(
            email=body.email,
            password=body.password,
        )
    except AuthenticationException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return {
        "code": 200,
        "data": {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "ai_calls_today": user.get("ai_calls_today", 0),
                "created_at": user["created_at"],
                "last_login": user.get("last_login"),
            },
            **tokens,
            "token_type": "bearer",
        },
        "message": "登录成功",
        "meta": {},
    }


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(req: Request, body: RefreshRequest):
    from app.core.auth import AuthManager
    from app.core.exceptions import InvalidTokenException, TokenExpiredException

    try:
        tokens = await AuthManager(db=req.app.state.db).refresh_token(body.refresh_token)
    except (TokenExpiredException, InvalidTokenException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return {
        "code": 200,
        "data": {**tokens, "token_type": "bearer"},
        "message": "Token刷新成功",
        "meta": {},
    }


@router.get("/me", response_model=ApiResponse)
async def me(user: dict = Depends(get_current_user)):
    return {
        "code": 200,
        "data": {"user": user},
        "message": "success",
        "meta": {},
    }
