"""Authentication API endpoints for TopicAI v4.0.

Handles user registration, login, token refresh, and current user retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.api.v1.deps import get_current_user
from app.models.common import ApiResponse

router = APIRouter()


# ==================== Request/Response Schemas ====================


class RegisterRequest(BaseModel):
    """User registration request body."""

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(
        ..., min_length=3, max_length=50, description="Username"
    )
    password: str = Field(
        ..., min_length=8, max_length=128, description="Password"
    )


class LoginRequest(BaseModel):
    """User login request body."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token refresh request body."""

    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseModel):
    """User information response."""

    id: str
    email: str
    username: str
    ai_calls_today: int
    created_at: str
    last_login: str | None = None


# ==================== Endpoints ====================


@router.post("/register", response_model=ApiResponse, status_code=201)
async def register(req: Request, request: RegisterRequest):
    """Register a new user account.

    Args:
        req: FastAPI request (for shared DB access).
        request: Registration details (email, username, password).

    Returns:
        User info with JWT tokens.
    """
    from app.core.auth import AuthManager
    from app.core.exceptions import UserAlreadyExistsException

    auth = AuthManager(db=req.app.state.db)
    try:
        user, tokens = await auth.register(
            email=request.email,
            username=request.username,
            password=request.password,
        )
        return {
            "code": 201,
            "data": {
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"],
                    "created_at": user["created_at"],
                },
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
            },
            "message": "注册成功",
            "meta": {},
        }
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.post("/login", response_model=ApiResponse)
async def login(req: Request, request: LoginRequest):
    """Authenticate a user and return JWT tokens.

    Args:
        req: FastAPI request (for shared DB access).
        request: Login credentials (email, password).

    Returns:
        JWT access and refresh tokens.
    """
    from app.core.auth import AuthManager
    from app.core.exceptions import AuthenticationException

    auth = AuthManager(db=req.app.state.db)
    try:
        user, tokens = await auth.login(
            email=request.email,
            password=request.password,
        )
        return {
            "code": 200,
            "data": {
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "username": user["username"],
                },
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "token_type": "bearer",
            },
            "message": "登录成功",
            "meta": {},
        }
    except AuthenticationException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(req: Request, request: RefreshRequest):
    """Refresh an expired access token.

    Args:
        req: FastAPI request (for shared DB access).
        request: Refresh token.

    Returns:
        New access token.
    """
    from app.core.auth import AuthManager
    from app.core.exceptions import InvalidTokenException, TokenExpiredException

    auth = AuthManager(db=req.app.state.db)
    try:
        new_tokens = await auth.refresh_token(request.refresh_token)
        return {
            "code": 200,
            "data": {
                "access_token": new_tokens["access_token"],
                "refresh_token": new_tokens["refresh_token"],
                "token_type": "bearer",
            },
            "message": "Token刷新成功",
            "meta": {},
        }
    except (TokenExpiredException, InvalidTokenException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@router.get("/me", response_model=ApiResponse)
async def me(user: dict = Depends(get_current_user)):
    """Get the currently authenticated user's information.

    Returns:
        Current user details.
    """
    return {
        "code": 200,
        "data": {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "ai_calls_today": user["ai_calls_today"],
                "created_at": user["created_at"],
                "last_login": user.get("last_login"),
            },
        },
        "message": "success",
        "meta": {},
    }
