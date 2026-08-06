"""Tests for T05: Authentication and rate limiting."""

from datetime import UTC, datetime, timedelta

import pytest


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class TestPasswordHashing:
    """TC05-09: Password hashing."""

    def test_hash_password_produces_bcrypt(self):
        """Given plaintext password, When hashed, Then bcrypt format."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        hashed = auth.hash_password("mysecurepassword")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_correct_password(self):
        """Given hashed password, When verifying correct password,
        Then returns True."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        hashed = auth.hash_password("correct")
        assert auth.verify_password("correct", hashed) is True

    def test_verify_wrong_password(self):
        """Given hashed password, When verifying wrong password,
        Then returns False."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        hashed = auth.hash_password("correct")
        assert auth.verify_password("wrong", hashed) is False

    def test_hash_is_not_plaintext(self):
        """Given plaintext password, When hashed, Then not equal to plaintext."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        hashed = auth.hash_password("secret123")
        assert hashed != "secret123"


class TestJWTToken:
    """TC05-05/06/07/08: JWT token operations."""

    def test_create_and_verify_access_token(self):
        """Given user_id, When creating access token, Then can verify and extract."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        token = auth.create_access_token("user-123")
        payload = auth.verify_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_create_and_verify_refresh_token(self):
        """Given user_id, When creating refresh token, Then type is refresh."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        token = auth.create_refresh_token("user-123")
        payload = auth._decode_token(token)
        assert payload["type"] == "refresh"

    def test_expired_token_raises_exception(self):
        """Given expired token, When verifying, Then TokenExpiredException."""
        from app.core.auth import AuthManager
        from app.core.exceptions import TokenExpiredException

        auth = AuthManager()
        token = auth.create_access_token(
            "user-123", expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(TokenExpiredException):
            auth.verify_token(token)

    def test_invalid_token_raises_exception(self):
        """Given garbage token, When verifying, Then InvalidTokenException."""
        from app.core.auth import AuthManager
        from app.core.exceptions import InvalidTokenException

        auth = AuthManager()
        with pytest.raises(InvalidTokenException):
            auth.verify_token("not.a.valid.token")

    def test_get_user_id_from_token(self):
        """Given valid token, When extracting user_id, Then correct."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        token = auth.create_access_token("user-456")
        user_id = auth.get_user_id_from_token(token)
        assert user_id == "user-456"

    def test_refresh_token_validation(self):
        """Given access token used where refresh expected, When checking type,
        Then token type is 'access' not 'refresh'."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        access_token = auth.create_access_token("user-123")
        payload = auth.verify_token(access_token)
        # Access token has type='access', not 'refresh'
        assert payload["type"] == "access"


class TestJWTIssuerAudience:
    """D1: JWT iss/aud validation."""

    def test_decode_accepts_valid_iss_aud(self):
        """Given token signed with configured iss/aud, When verifying,
        Then payload is returned with iss/aud claims."""
        from app.core.auth import AuthManager

        auth = AuthManager()
        token = auth.create_access_token("user-iss-ok")
        payload = auth.verify_token(token)
        assert payload["sub"] == "user-iss-ok"
        assert payload["iss"] == auth.settings.jwt_iss
        assert payload["aud"] == auth.settings.jwt_aud

    def test_decode_rejects_wrong_iss(self):
        """Given token signed with wrong iss, When verifying,
        Then InvalidTokenException is raised."""
        import jwt as pyjwt

        from app.core.auth import AuthManager
        from app.core.exceptions import InvalidTokenException

        auth = AuthManager()
        # Forge a token with a bogus iss but correct secret/aud.
        from datetime import UTC, datetime, timedelta

        now = datetime.now(UTC)
        payload = {
            "sub": "user-bad-iss",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "access",
            "iss": "evil-issuer",
            "aud": auth.settings.jwt_aud,
        }
        token = pyjwt.encode(
            payload,
            auth.settings.jwt_secret_key,
            algorithm=auth.settings.jwt_algorithm,
        )
        with pytest.raises(InvalidTokenException):
            auth.verify_token(token)

    def test_decode_rejects_wrong_aud(self):
        """Given token signed with wrong aud, When verifying,
        Then InvalidTokenException is raised."""
        import jwt as pyjwt

        from app.core.auth import AuthManager
        from app.core.exceptions import InvalidTokenException

        auth = AuthManager()
        from datetime import UTC, datetime, timedelta

        now = datetime.now(UTC)
        payload = {
            "sub": "user-bad-aud",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "access",
            "iss": auth.settings.jwt_iss,
            "aud": "evil-audience",
        }
        token = pyjwt.encode(
            payload,
            auth.settings.jwt_secret_key,
            algorithm=auth.settings.jwt_algorithm,
        )
        with pytest.raises(InvalidTokenException):
            auth.verify_token(token)

    def test_decode_rejects_missing_iss_aud(self):
        """Given token lacking iss/aud claims, When verifying,
        Then InvalidTokenException is raised (D1 contract)."""
        import jwt as pyjwt

        from app.core.auth import AuthManager
        from app.core.exceptions import InvalidTokenException

        auth = AuthManager()
        from datetime import UTC, datetime, timedelta

        now = datetime.now(UTC)
        payload = {
            "sub": "user-no-claims",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "access",
            # NOTE: no iss/aud — must be rejected
        }
        token = pyjwt.encode(
            payload,
            auth.settings.jwt_secret_key,
            algorithm=auth.settings.jwt_algorithm,
        )
        with pytest.raises(InvalidTokenException):
            auth.verify_token(token)


class TestExceptions:
    """TC05-15/16/17: Exception handling."""

    def test_app_exception_has_status_code(self):
        """Given AppException, When created, Then has status_code."""
        from app.core.exceptions import AppException

        exc = AppException("test", status_code=400, error_code="TEST")
        assert exc.status_code == 400
        assert exc.error_code == "TEST"

    def test_rate_limit_exception_default_message(self):
        """Given RateLimitException, When created,
        Then has user-friendly Chinese message."""
        from app.core.exceptions import RateLimitException

        exc = RateLimitException()
        assert "频繁" in exc.message
        assert exc.status_code == 429

    def test_llm_exception_user_friendly(self):
        """Given LLMException, When created, Then has 503 status."""
        from app.core.exceptions import LLMException

        exc = LLMException(provider="openai_compatible")
        assert exc.status_code == 503
        assert exc.provider == "openai_compatible"

    def test_authentication_exception(self):
        """Given AuthenticationException, When created, Then 401 status."""
        from app.core.exceptions import AuthenticationException

        exc = AuthenticationException("密码错误")
        assert exc.status_code == 401

    def test_user_already_exists_exception(self):
        """Given UserAlreadyExistsException, When created, Then 409 status."""
        from app.core.exceptions import UserAlreadyExistsException

        exc = UserAlreadyExistsException()
        assert exc.status_code == 409
