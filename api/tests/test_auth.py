"""Tests for authentication utilities."""

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from gen_ai_on_aws.auth import create_auth_dependency, verify_webhook_auth


class TestVerifyWebhookAuth:
    """Test cases for verify_webhook_auth function."""

    @pytest.mark.asyncio
    async def test_successful_auth(self):
        """Test successful authentication."""
        with patch.dict(os.environ, {"ELEVENLABS_WEBHOOK_AUTH": "valid-token"}):
            result = await verify_webhook_auth("valid-token")
            assert result == "valid-token"

    @pytest.mark.asyncio
    async def test_missing_auth_header(self):
        """Test missing auth header."""
        with patch.dict(os.environ, {"ELEVENLABS_WEBHOOK_AUTH": "valid-token"}):
            with pytest.raises(HTTPException) as exc_info:
                await verify_webhook_auth(None)
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Missing authentication header"

    @pytest.mark.asyncio
    async def test_invalid_auth_header(self):
        """Test invalid auth header."""
        with patch.dict(os.environ, {"ELEVENLABS_WEBHOOK_AUTH": "valid-token"}):
            with pytest.raises(HTTPException) as exc_info:
                await verify_webhook_auth("invalid-token")
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Unauthorized"

    @pytest.mark.asyncio
    async def test_missing_env_var(self):
        """Test when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                await verify_webhook_auth("any-token")
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Webhook authentication not configured"


class TestCreateAuthDependency:
    """Test cases for create_auth_dependency factory."""

    @pytest.mark.asyncio
    async def test_custom_auth_dependency(self):
        """Test creating a custom auth dependency."""
        with patch.dict(os.environ, {"CUSTOM_AUTH": "custom-token"}):
            verify_custom = create_auth_dependency("CUSTOM_AUTH", "x-api-key")
            result = await verify_custom("custom-token")
            assert result == "custom-token"

    @pytest.mark.asyncio
    async def test_custom_auth_invalid(self):
        """Test custom auth dependency with invalid token."""
        with patch.dict(os.environ, {"CUSTOM_AUTH": "custom-token"}):
            verify_custom = create_auth_dependency("CUSTOM_AUTH", "x-api-key")
            with pytest.raises(HTTPException) as exc_info:
                await verify_custom("wrong-token")
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Unauthorized"

    @pytest.mark.asyncio
    async def test_custom_auth_missing_env(self):
        """Test custom auth dependency when env var is missing."""
        with patch.dict(os.environ, {}, clear=True):
            verify_custom = create_auth_dependency("CUSTOM_AUTH", "x-api-key")
            with pytest.raises(HTTPException) as exc_info:
                await verify_custom("any-token")
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Authentication not configured"
