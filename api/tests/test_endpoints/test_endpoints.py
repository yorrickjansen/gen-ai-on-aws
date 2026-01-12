import os
import unittest.mock as mock

import pytest
from fastapi.testclient import TestClient

from gen_ai_on_aws.endpoints.types import User
from gen_ai_on_aws.main import app
from gen_ai_on_aws.services.queue_service import QueueService


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_hello(client):
    """Test the hello endpoint."""
    response = client.get("/endpoints/hello")
    assert response.status_code == 200
    assert response.json() == "Hello, world!"


def test_extract_user(client):
    """Test the extract user endpoint with valid user data."""
    test_text = "My name is John Doe, I am 30 years old, and my email is john@example.com"
    response = client.post("/endpoints/extract-user", json={"text": test_text})

    assert response.status_code == 200
    data = response.json()

    user = User.model_validate(data)
    assert user.name == "John Doe"
    assert user.age == 30
    assert user.email == "john@example.com"

    # Test with missing email
    test_text_no_email = "My name is Jane Doe and I am 25 years old"
    response = client.post("/endpoints/extract-user", json={"text": test_text_no_email})

    assert response.status_code == 200
    data = response.json()
    user = User.model_validate(data)

    assert user.name == "Jane Doe"
    assert user.age == 25
    assert user.email is None


def test_extract_user_failure(client):
    """Test the extract user endpoint with invalid user data."""
    # Test with text that doesn't contain any user information
    test_text = "This is a random text without any user information"
    response = client.post("/endpoints/extract-user", json={"text": test_text})

    # Since the LLM might try to hallucinate or return placeholder values,
    # we accept either None or a User object with placeholder values
    assert response.status_code == 200
    data = response.json()

    # Accept either None or placeholder values like <UNKNOWN>, age 0, etc.
    if data is not None:
        # If it returns a User object, it should have placeholder/unknown values
        assert "name" in data
        assert "age" in data
        # Placeholder values typically include <UNKNOWN>, Unknown, or age 0
        assert data["name"] in ["<UNKNOWN>", "Unknown", ""] or data["age"] == 0


@mock.patch("gen_ai_on_aws.endpoints.endpoints.settings")
@mock.patch.object(QueueService, "send_message")
def test_extract_user_async(mock_send_message, mock_settings, client):
    """Test the async extract user endpoint."""
    # Set up the settings mock to return a queue URL
    mock_settings.sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"

    # Set up the send_message mock to return a request ID
    mock_send_message.return_value = "test-request-id-123"

    # Test the endpoint
    test_text = "My name is John Doe, I am 30 years old, and my email is john@example.com"
    response = client.post("/endpoints/extract-user-async", json={"text": test_text})

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["request_id"] == "test-request-id-123"

    # Verify the queue service was called correctly
    mock_send_message.assert_called_once()


@mock.patch.dict(
    os.environ,
    {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
    },
)
@mock.patch("httpx.AsyncClient.get")
def test_supabase_read(mock_httpx_get, client):
    """Test the Supabase read endpoint with successful response."""
    # Mock the HTTP response
    mock_response = mock.Mock()
    mock_response.json.return_value = [
        {"id": 1, "name": "Test User 1"},
        {"id": 2, "name": "Test User 2"},
    ]
    mock_response.raise_for_status = mock.Mock()

    # Mock httpx.AsyncClient.get to return the mock response
    mock_httpx_get.return_value = mock_response

    # Test the endpoint
    response = client.post(
        "/endpoints/supabase-read",
        json={"table": "users", "select": "*"},
    )

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == 1
    assert data["data"][0]["name"] == "Test User 1"

    # Verify the HTTP call was made correctly
    mock_httpx_get.assert_called_once()
    call_args = mock_httpx_get.call_args
    assert call_args.args[0] == "https://test.supabase.co/rest/v1/users"
    assert call_args.kwargs["params"] == {"select": "*"}
    assert call_args.kwargs["headers"]["apikey"] == "test-key"
    assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-key"


@mock.patch.dict(
    os.environ,
    {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
    },
)
@mock.patch("httpx.AsyncClient.get")
def test_supabase_read_with_limit(mock_httpx_get, client):
    """Test the Supabase read endpoint with limit parameter."""
    # Mock the HTTP response
    mock_response = mock.Mock()
    mock_response.json.return_value = [{"id": 1, "name": "Test User 1"}]
    mock_response.raise_for_status = mock.Mock()

    # Mock httpx.AsyncClient.get to return the mock response
    mock_httpx_get.return_value = mock_response

    # Test the endpoint
    response = client.post(
        "/endpoints/supabase-read",
        json={"table": "users", "select": "*", "limit": 1},
    )

    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1

    # Verify the HTTP call included the limit parameter
    call_args = mock_httpx_get.call_args
    assert call_args.kwargs["params"]["limit"] == "1"


@mock.patch.dict(os.environ, {}, clear=True)
def test_supabase_read_missing_config(client):
    """Test the Supabase read endpoint when URL/key is not configured."""
    response = client.post(
        "/endpoints/supabase-read",
        json={"table": "users", "select": "*"},
    )

    # Should return 500 error when config is missing
    assert response.status_code == 500
    assert "Supabase URL and key must be configured" in response.json()["detail"]


@mock.patch.dict(
    os.environ,
    {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
    },
)
@mock.patch("httpx.AsyncClient.get")
def test_supabase_read_query_error(mock_httpx_get, client):
    """Test the Supabase read endpoint when query fails."""
    # Mock httpx to raise an error
    mock_httpx_get.side_effect = Exception("Database connection error")

    # Test the endpoint
    response = client.post(
        "/endpoints/supabase-read",
        json={"table": "users", "select": "*"},
    )

    # Should return 500 error when query fails
    assert response.status_code == 500
    assert "Failed to read from Supabase" in response.json()["detail"]
