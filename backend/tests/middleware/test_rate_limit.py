from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import RateLimitException
from app.middleware.rate_limit import RateLimitMiddleware


def request(path: str):
    value = MagicMock()
    value.url.path = path
    value.client.host = "127.0.0.1"
    return value


@pytest.mark.asyncio
async def test_v2_auth_path_is_rate_limited():
    limiter = MagicMock()
    limiter.check_and_increment.side_effect = RateLimitException()
    middleware = RateLimitMiddleware(MagicMock(), limiter=limiter)
    next_handler = AsyncMock()

    response = await middleware.dispatch(request("/api/v2/auth/login"), next_handler)

    assert response.status_code == 429
    next_handler.assert_not_called()


@pytest.mark.asyncio
async def test_removed_v1_path_has_no_special_handling():
    limiter = MagicMock()
    middleware = RateLimitMiddleware(MagicMock(), limiter=limiter)
    next_handler = AsyncMock(return_value="ok")

    assert await middleware.dispatch(request("/api/v1/auth/login"), next_handler) == "ok"
    limiter.check_and_increment.assert_not_called()
