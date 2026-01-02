import os
import pytest
from pydantic import ValidationError
from coreason_identity.models import UserContext
from coreason_identity.config import CoreasonIdentityConfig


def test_user_context_valid():
    user = UserContext(
        sub="user123",
        email="test@example.com",
        project_context="proj1",
        permissions=["read", "write"],
    )
    assert user.sub == "user123"
    assert user.email == "test@example.com"
    assert user.project_context == "proj1"
    assert user.permissions == ["read", "write"]


def test_user_context_defaults():
    user = UserContext(sub="user123", email="test@example.com")
    assert user.project_context is None
    assert user.permissions == []


def test_user_context_invalid_email():
    with pytest.raises(ValidationError):
        UserContext(sub="user123", email="not-an-email")


def test_config_env_vars():
    os.environ["COREASON_AUTH_DOMAIN"] = "test.auth0.com"
    os.environ["COREASON_AUTH_AUDIENCE"] = "api://test"

    config = CoreasonIdentityConfig()
    assert config.domain == "test.auth0.com"
    assert config.audience == "api://test"

    del os.environ["COREASON_AUTH_DOMAIN"]
    del os.environ["COREASON_AUTH_AUDIENCE"]


def test_config_missing_vars():
    # Ensure env vars are cleared
    if "COREASON_AUTH_DOMAIN" in os.environ:
        del os.environ["COREASON_AUTH_DOMAIN"]
    if "COREASON_AUTH_AUDIENCE" in os.environ:
        del os.environ["COREASON_AUTH_AUDIENCE"]

    with pytest.raises(ValidationError):
        CoreasonIdentityConfig()
