"""Tests for the 11Labs webhook endpoint."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from gen_ai_on_aws.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def valid_webhook_payload():
    """Create a valid webhook payload."""
    return {
        "caller_id": "+19093586520",
        "agent_id": "agent_6201kbkk9f2de3ma3ntvjg7xdxs9",
        "called_number": "+498941434322",
        "call_sid": "CAb6906d9b35edb6666562caea0fb1d1aa",
        "conversation_id": "conv_3701kesxp7rzfs5v51w069egjdvf",
    }


@pytest.fixture
def mock_supabase_response():
    """Mock Supabase response data."""
    return [
        {
            "id": "location1",
            "location_name": "Test Hotel",
            "check_in_support_type": "24/7",
            "website_url": "https://test-hotel.com",
            "contact_email": "info@test-hotel.com",
            "phone_number": {
                "id": "phone1",
                "phone_number": "+498941434322",
                "aura_account": {
                    "name": "Test Hotel Group",
                    "test_account": False,
                    "hotel_category": "luxury",
                    "preferred_currency": "EUR",
                },
                "agent_config": {
                    "welcomeMessage": "Welcome to Test Hotel",
                    "agentName": "Assistant",
                    "formOfAddress": "Formal",
                },
            },
        }
    ]


class TestElevenLabsWebhook:
    """Test cases for the 11Labs webhook endpoint."""

    def test_missing_auth_header(self, client):
        """Test that missing auth header returns 401."""
        with patch.dict(os.environ, {"ELEVENLABS_WEBHOOK_AUTH": "test-auth-token"}):
            response = client.post(
                "/endpoints/elevenlabs-webhook",
                json={
                    "caller_id": "+19093586520",
                    "agent_id": "test_agent",
                    "called_number": "+498941434322",
                    "call_sid": "test_sid",
                    "conversation_id": "test_conversation",
                },
            )
            assert response.status_code == 401

    def test_invalid_auth_header(self, client):
        """Test that invalid auth header returns 401."""
        with patch.dict(os.environ, {"ELEVENLABS_WEBHOOK_AUTH": "test-auth-token"}):
            response = client.post(
                "/endpoints/elevenlabs-webhook",
                json={
                    "caller_id": "+19093586520",
                    "agent_id": "test_agent",
                    "called_number": "+498941434322",
                    "call_sid": "test_sid",
                    "conversation_id": "test_conversation",
                },
                headers={"auth": "wrong-token"},
            )
            assert response.status_code == 401

    def test_blacklisted_number(self, client, valid_webhook_payload):
        """Test that blacklisted numbers are blocked."""
        with patch.dict(
            os.environ,
            {
                "ELEVENLABS_WEBHOOK_AUTH": "test-auth-token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
            },
        ):
            # Use a blacklisted number
            valid_webhook_payload["caller_id"] = "+41793000161"
            response = client.post(
                "/endpoints/elevenlabs-webhook",
                json=valid_webhook_payload,
                headers={"auth": "test-auth-token"},
            )
            assert response.status_code == 200
            assert response.json()["dynamic_variables"]["error"] == "Number blocked"

    @pytest.mark.asyncio
    async def test_successful_webhook(self, client, valid_webhook_payload, mock_supabase_response):
        """Test successful webhook processing."""
        with patch.dict(
            os.environ,
            {
                "ELEVENLABS_WEBHOOK_AUTH": "test-auth-token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
            },
        ):
            # Mock the httpx client
            mock_response = AsyncMock()
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = lambda: mock_supabase_response

            with patch("httpx.AsyncClient.get", return_value=mock_response):
                response = client.post(
                    "/endpoints/elevenlabs-webhook",
                    json=valid_webhook_payload,
                    headers={"auth": "test-auth-token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "dynamic_variables" in data
                assert data["dynamic_variables"]["host_name"] == "Test Hotel Group"
                assert data["dynamic_variables"]["mode"] == "single-location"
                assert data["dynamic_variables"]["formatted_user_number"] == "+1 - 909 - 358 - 6520"

    @pytest.mark.asyncio
    async def test_no_data_found(self, client, valid_webhook_payload):
        """Test when no configuration is found in Supabase."""
        with patch.dict(
            os.environ,
            {
                "ELEVENLABS_WEBHOOK_AUTH": "test-auth-token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key",
            },
        ):
            # Mock empty response from Supabase
            mock_response = AsyncMock()
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = lambda: []

            with patch("httpx.AsyncClient.get", return_value=mock_response):
                response = client.post(
                    "/endpoints/elevenlabs-webhook",
                    json=valid_webhook_payload,
                    headers={"auth": "test-auth-token"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["dynamic_variables"]["error"] == "Could not find client configuration"

    def test_phone_number_formatting(self):
        """Test phone number formatting function."""
        from gen_ai_on_aws.endpoints.endpoints import _format_phone_number

        # Test US number
        assert _format_phone_number("+19093586520") == "+1 - 909 - 358 - 6520"

        # Test German number
        assert _format_phone_number("+491234567890") == "+49 - 123 - 456 - 789 - 0"

        # Test anonymous
        assert _format_phone_number("Anonymous") == "Anonymous"

        # Test empty
        assert _format_phone_number("") == "Anonymous"

    def test_sms_capability(self):
        """Test SMS capability detection."""
        from gen_ai_on_aws.endpoints.endpoints import _can_receive_sms

        # Test German mobile number
        assert _can_receive_sms("+491701234567") is True

        # Test German landline
        assert _can_receive_sms("+493012345678") is False

        # Test US number (assumed capable)
        assert _can_receive_sms("+19093586520") is True

        # Test anonymous
        assert _can_receive_sms("Anonymous") is False
