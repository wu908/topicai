"""Regression tests for configuration fail-open defects.

Covers two settings that accepted any string and degraded silently:

* ``ENVIRONMENT`` accepted any value, so a typo (``producton``) made
  :attr:`Settings.is_production` False and disabled the production
  JWT-secret strength gate in ``backend/main.py`` — a fail-open path.
* ``JWT_ALGORITHM`` accepted any value, including ``none`` (unsigned
  tokens) and asymmetric algorithms verified against the HMAC secret.
"""

import pytest
from pydantic import ValidationError

from config.settings import Settings


def _reset_settings() -> None:
    import config.settings as settings_module

    settings_module._settings = None


@pytest.fixture(autouse=True)
def reset_settings_after_test():
    yield
    _reset_settings()


# ==================== ENVIRONMENT ====================


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("production", "production"),
        ("PRODUCTION", "production"),
        ("  Production  ", "production"),
        ("prod", "production"),
    ],
)
def test_production_aliases_normalize_to_production(monkeypatch, raw, expected):
    """``prod``/casing/whitespace must still be recognised as production.

    Otherwise the JWT-secret strength gate fails open.
    """
    monkeypatch.setenv("ENVIRONMENT", raw)

    settings = Settings()

    assert settings.environment == expected
    assert settings.is_production is True


@pytest.mark.parametrize("raw", ["producton", "prodution", "", "live", "nonsense"])
def test_unknown_environment_fails_loudly(monkeypatch, raw):
    """An unrecognised environment must abort startup, not degrade silently."""
    monkeypatch.setenv("ENVIRONMENT", raw)

    with pytest.raises(ValidationError, match="ENVIRONMENT must be one of"):
        Settings()


def test_development_alias_is_not_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "dev")

    settings = Settings()

    assert settings.is_development is True
    assert settings.is_production is False


# ==================== JWT_ALGORITHM ====================


@pytest.mark.parametrize("raw", ["none", "NONE", "RS256", "ES256", "HS999", ""])
def test_unsupported_jwt_algorithm_is_rejected(monkeypatch, raw):
    """``none`` would yield unsigned tokens; asymmetric algs would be
    verified against the HMAC secret."""
    monkeypatch.setenv("JWT_ALGORITHM", raw)

    with pytest.raises(ValidationError, match="JWT_ALGORITHM must be one of"):
        Settings()


@pytest.mark.parametrize("raw", ["HS256", "hs384", " HS512 "])
def test_supported_jwt_algorithms_normalize(monkeypatch, raw):
    monkeypatch.setenv("JWT_ALGORITHM", raw)

    settings = Settings()

    assert settings.jwt_algorithm == raw.strip().upper()
