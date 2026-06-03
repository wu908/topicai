"""User-related Pydantic schemas for TopicAI v4.0.

Defines schemas for user registration, login, and profile responses.
"""


from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration request.

    Attributes:
        email: User email address (validated).
        username: Unique username (3-50 chars).
        password: Plaintext password (min 8 chars, hashed before storage).
    """

    email: EmailStr = Field(..., description="User email address")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password",
    )


class UserLogin(BaseModel):
    """Schema for user login request.

    Attributes:
        email: User email address.
        password: Plaintext password.
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Plaintext password")


class UserResponse(BaseModel):
    """Schema for user data in API responses.

    Does NOT include password_hash or other sensitive fields.

    Attributes:
        id: Unique user ID (UUID).
        email: User email address.
        username: Username.
        ai_calls_today: AI calls made today.
        created_at: Account creation timestamp.
        last_login: Last login timestamp (optional).
    """

    id: str = Field(..., description="User ID (UUID)")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    ai_calls_today: int = Field(
        default=0, ge=0, description="AI calls made today"
    )
    created_at: str = Field(..., description="Account creation timestamp")
    last_login: str | None = Field(
        default=None, description="Last login timestamp"
    )


class TokenPair(BaseModel):
    """Schema for JWT token pair response.

    Attributes:
        access_token: Short-lived access token (30 min).
        refresh_token: Long-lived refresh token (7 days).
        token_type: Token type (always 'bearer').
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
