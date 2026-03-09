"""Unit tests for Settings model_validator (check_secret_key_in_production)."""
import pytest
from pydantic import ValidationError

from app.config import Settings

DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"


def test_validator_raises_when_production_with_default_secret():
    """Validator must raise ValueError when DEBUG=False and SECRET_KEY is the default."""
    with pytest.raises((ValueError, ValidationError)):
        Settings(DEBUG=False, SECRET_KEY=DEFAULT_SECRET_KEY)


def test_validator_ok_when_production_with_custom_secret():
    """Validator must NOT raise when DEBUG=False and SECRET_KEY is a non-default value."""
    settings = Settings(DEBUG=False, SECRET_KEY="my-secure-secret")
    assert settings.SECRET_KEY == "my-secure-secret"
    assert settings.DEBUG is False


def test_validator_ok_when_debug_mode_with_default_secret():
    """Validator must NOT raise when DEBUG=True even if SECRET_KEY is the default."""
    settings = Settings(DEBUG=True, SECRET_KEY=DEFAULT_SECRET_KEY)
    assert settings.SECRET_KEY == DEFAULT_SECRET_KEY
    assert settings.DEBUG is True
