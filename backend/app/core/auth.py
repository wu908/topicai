"""JWT Authentication module for TopicAI v4.0.

Handles user registration, login, token generation/validation/refresh,
and password hashing with bcrypt.

Uses PyJWT for JWT and passlib for password hashing.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from config.settings import get_settings

if TYPE_CHECKING:
    from app.core.database import Database

logger = logging.getLogger(__name__)

# Password hashing context (bcrypt)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthManager:
    """Manager for JWT authentication and user management.

    Handles user registration, login, token operations, and password hashing.
    """

    def __init__(self, db: Database | None = None):
        """Initialize AuthManager with application settings.

        Args:
            db: Optional shared Database instance. If provided, methods reuse
                it instead of creating new connections per request.
        """
        self.settings = get_settings()
        self._pwd_context = _pwd_context
        self._db = db

    # ==================== Password Hashing ====================

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password using bcrypt.

        Args:
            password: Plaintext password.

        Returns:
            Bcrypt hash string.
        """
        return self._pwd_context.hash(password)

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify a password against its bcrypt hash.

        Args:
            plain_password: Plaintext password to check.
            hashed_password: Bcrypt hash to verify against.

        Returns:
            True if password matches hash.
        """
        return self._pwd_context.verify(plain_password, hashed_password)

    # ==================== Token Operations ====================

    def create_access_token(
        self, user_id: str, expires_delta: timedelta | None = None
    ) -> str:
        """Create a JWT access token.

        Args:
            user_id: The user's unique ID.
            expires_delta: Custom expiry duration. Defaults to settings value.

        Returns:
            Encoded JWT access token string.
        """
        if expires_delta is None:
            expires_delta = timedelta(
                minutes=self.settings.jwt_access_token_expire_minutes
            )

        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "sub": user_id,
            "iat": now,
            "exp": expire,
            "type": "access",
        }

        return jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def create_refresh_token(
        self, user_id: str, expires_delta: timedelta | None = None
    ) -> str:
        """Create a JWT refresh token.

        Args:
            user_id: The user's unique ID.
            expires_delta: Custom expiry duration. Defaults to settings value.

        Returns:
            Encoded JWT refresh token string.
        """
        if expires_delta is None:
            expires_delta = timedelta(
                days=self.settings.jwt_refresh_token_expire_days
            )

        now = datetime.now(UTC)
        expire = now + expires_delta

        payload = {
            "sub": user_id,
            "iat": now,
            "exp": expire,
            "type": "refresh",
        }

        return jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def _decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT token (internal, no type check).

        Args:
            token: The JWT token string.

        Returns:
            Decoded token payload as dictionary.

        Raises:
            TokenExpiredException: If token has expired.
            InvalidTokenException: If token is malformed or invalid.
        """
        from app.core.exceptions import InvalidTokenException, TokenExpiredException

        try:
            return jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
        except ExpiredSignatureError:
            raise TokenExpiredException("Token has expired") from None
        except InvalidTokenError as e:
            raise InvalidTokenException(f"Invalid token: {str(e)}") from e

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT access token.

        Args:
            token: The JWT token string.

        Returns:
            Decoded token payload as dictionary.

        Raises:
            TokenExpiredException: If token has expired.
            InvalidTokenException: If token is malformed, invalid, or not an access token.
        """
        from app.core.exceptions import InvalidTokenException

        payload = self._decode_token(token)
        if payload.get("type") != "access":
            raise InvalidTokenException("Not an access token")
        return payload

    def get_user_id_from_token(self, token: str) -> str:
        """Extract user_id from a valid JWT token.

        Args:
            token: The JWT token string.

        Returns:
            User ID string.

        Raises:
            TokenExpiredException: If token has expired.
            InvalidTokenException: If token is invalid.
        """
        payload = self.verify_token(token)
        return payload["sub"]

    # ==================== User Management ====================

    async def register(
        self, email: str, username: str, password: str
    ) -> tuple[dict, dict]:
        """Register a new user.

        Args:
            email: User's email address.
            username: Username.
            password: Plaintext password.

        Returns:
            Tuple of (user_dict, tokens_dict).

        Raises:
            UserAlreadyExistsException: If email or username is taken.
        """
        from app.core.database import Database
        from app.core.exceptions import UserAlreadyExistsException

        db = self._db or Database(self.settings.database_url)
        if not self._db:
            await db.init_db()

        # Check for existing user
        existing = await db.fetch_one(
            "SELECT id FROM users WHERE email = :email OR username = :username",
            {"email": email, "username": username},
        )
        if existing:
            if not self._db:
                await db.close()
            raise UserAlreadyExistsException(
                "该邮箱或用户名已被注册"
            )

        # Create user
        user_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0)
        reset_at = reset_at.replace(day=reset_at.day + 1)

        password_hash = self.hash_password(password)

        user_data = {
            "id": user_id,
            "email": email,
            "username": username,
            "password_hash": password_hash,
            "ai_calls_today": 0,
            "ai_calls_reset_at": reset_at.isoformat().replace("+00:00", "Z"),
            "created_at": now.isoformat().replace("+00:00", "Z"),
            "last_login": now.isoformat().replace("+00:00", "Z"),
        }

        await db.insert("users", user_data)
        if not self._db:
            await db.close()

        # Generate tokens
        access_token = self.create_access_token(user_id)
        refresh_token = self.create_refresh_token(user_id)

        user_dict = {
            "id": user_id,
            "email": email,
            "username": username,
            "ai_calls_today": 0,
            "created_at": user_data["created_at"],
            "last_login": user_data["last_login"],
        }

        tokens_dict = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

        return user_dict, tokens_dict

    async def login(
        self, email: str, password: str
    ) -> tuple[dict, dict]:
        """Authenticate a user and return tokens.

        Args:
            email: User's email address.
            password: Plaintext password.

        Returns:
            Tuple of (user_dict, tokens_dict).

        Raises:
            AuthenticationException: If credentials are invalid.
        """
        from app.core.database import Database
        from app.core.exceptions import AuthenticationException

        db = self._db or Database(self.settings.database_url)
        if not self._db:
            await db.init_db()

        # Find user
        user = await db.fetch_one(
            "SELECT * FROM users WHERE email = :email",
            {"email": email},
        )
        if not user:
            if not self._db:
                await db.close()
            raise AuthenticationException("邮箱或密码错误")

        # Verify password
        if not self.verify_password(password, user["password_hash"]):
            if not self._db:
                await db.close()
            raise AuthenticationException("邮箱或密码错误")

        # Update last_login
        now = datetime.now(UTC)
        await db.update(
            "users",
            {"last_login": now.isoformat().replace("+00:00", "Z")},
            {"id": user["id"]},
        )

        if not self._db:
            await db.close()

        # Generate tokens
        access_token = self.create_access_token(user["id"])
        refresh_token = self.create_refresh_token(user["id"])

        user_dict = {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "ai_calls_today": user["ai_calls_today"],
            "created_at": user["created_at"],
            "last_login": user["last_login"],
        }

        tokens_dict = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

        return user_dict, tokens_dict

    async def refresh_token(self, refresh_token: str) -> dict:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: The refresh token.

        Returns:
            New tokens dictionary.

        Raises:
            TokenExpiredException: If refresh token is expired.
            InvalidTokenException: If refresh token is invalid.
        """
        from app.core.exceptions import InvalidTokenException

        payload = self._decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise InvalidTokenException("Not a refresh token")

        user_id = payload["sub"]

        # Generate new token pair
        new_access_token = self.create_access_token(user_id)
        new_refresh_token = self.create_refresh_token(user_id)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def get_user(self, user_id: str) -> dict | None:
        """Get a user by ID.

        Args:
            user_id: The user's unique ID.

        Returns:
            User dictionary or None if not found.
        """
        from app.core.database import Database

        db = self._db or Database(self.settings.database_url)
        if not self._db:
            await db.init_db()

        user = await db.fetch_one(
            "SELECT * FROM users WHERE id = :id",
            {"id": user_id},
        )

        if not self._db:
            await db.close()
        return user
