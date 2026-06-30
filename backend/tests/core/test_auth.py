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


class TestRateLimiter:
    """TC05-10/11/12: Rate limiting."""

    def test_first_call_succeeds(self):
        """Given new user, When first AI call, Then returns remaining quota."""
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_calls=20)
        result = limiter.check_and_increment("new-user")
        assert result["remaining"] == 19
        assert result["used"] == 1

    def test_20_calls_succeed(self, monkeypatch):
        """Given user, When making 20 calls, Then all succeed."""
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_calls=20)
        for i in range(20):
            result = limiter.check_and_increment("test-user")
            assert result["remaining"] == 19 - i

    def test_21st_call_raises_exception(self):
        """Given user with 20 calls, When 21st call, Then RateLimitException."""
        from app.core.exceptions import RateLimitException
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_calls=20)
        for _ in range(20):
            limiter.check_and_increment("test-user-2")

        with pytest.raises(RateLimitException):
            limiter.check_and_increment("test-user-2")

    def test_get_remaining_without_incrementing(self):
        """Given user with calls, When get_remaining, Then count unchanged."""
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_calls=20)
        limiter.check_and_increment("user-a")
        limiter.check_and_increment("user-a")

        remaining = limiter.get_remaining("user-a")
        assert remaining["used"] == 2
        assert remaining["remaining"] == 18

        # Check again — should not have incremented
        remaining2 = limiter.get_remaining("user-a")
        assert remaining2["used"] == 2

    def test_different_users_independent(self):
        """Given two users, When each makes calls, Then counts independent."""
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_calls=20)
        limiter.check_and_increment("user-1")
        limiter.check_and_increment("user-1")
        limiter.check_and_increment("user-2")

        r1 = limiter.get_remaining("user-1")
        r2 = limiter.get_remaining("user-2")
        assert r1["used"] == 2
        assert r2["used"] == 1

    def test_reset_user(self):
        """Given user with calls, When reset_user, Then count back to 0."""
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_calls=20)
        for _ in range(5):
            limiter.check_and_increment("reset-user")

        limiter.reset_user("reset-user")
        remaining = limiter.get_remaining("reset-user")
        assert remaining["used"] == 0

    def test_reset_at_midnight_utc(self):
        """Given rate limiter, When checking reset_at, Then is UTC midnight."""
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_calls=20)
        result = limiter.check_and_increment("midnight-user")
        assert "reset_at" in result
        assert "T00:00:00" in result["reset_at"] or "Z" in result["reset_at"]

    def test_reset_at_month_end_rolls_over(self, monkeypatch):
        """Regression: on the last day of a 30-day month, reset_at must roll
        into the next month instead of raising ValueError(day=31)."""
        import app.core.rate_limiter as rl

        fixed = datetime(2026, 6, 30, 23, 59, 59, tzinfo=UTC)

        class _FixedDT(datetime):
            @classmethod
            def now(cls, tz=None):
                return fixed

        monkeypatch.setattr(rl, "datetime", _FixedDT)

        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter(max_calls=20)
        result = limiter.check_and_increment("month-end-user")
        assert result["reset_at"] == "2026-07-01T00:00:00Z"


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
        assert "今日" in exc.message
        assert exc.status_code == 429

    def test_llm_exception_user_friendly(self):
        """Given LLMException, When created, Then has 503 status."""
        from app.core.exceptions import LLMException

        exc = LLMException(provider="deepseek")
        assert exc.status_code == 503
        assert exc.provider == "deepseek"

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

    def test_validation_exception(self):
        """Given ValidationException, When created, Then 422 status."""
        from app.core.exceptions import ValidationException

        exc = ValidationException(details={"field": "error"})
        assert exc.status_code == 422

    def test_not_found_exception(self):
        """Given NotFoundException, When created, Then 404 status."""
        from app.core.exceptions import NotFoundException

        exc = NotFoundException(resource_type="user", resource_id="123")
        assert exc.status_code == 404
