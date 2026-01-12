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
@mock.patch("gen_ai_on_aws.endpoints.endpoints.acreate_client")
def test_supabase_read(mock_acreate_client, client):
    """Test the Supabase read endpoint with successful response."""
    # Mock the Supabase client response
    mock_client = mock.Mock()
    mock_table = mock.Mock()
    mock_select = mock.Mock()
    mock_response = mock.Mock()
    mock_response.data = [
        {"id": 1, "name": "Test User 1"},
        {"id": 2, "name": "Test User 2"},
    ]

    # Chain the mock calls
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.execute = mock.AsyncMock(return_value=mock_response)

    # Mock acreate_client to return the mock client when awaited
    async def mock_create(url, key):
        return mock_client

    mock_acreate_client.side_effect = mock_create

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


@mock.patch.dict(
    os.environ,
    {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
    },
)
@mock.patch("gen_ai_on_aws.endpoints.endpoints.acreate_client")
def test_supabase_read_with_limit(mock_acreate_client, client):
    """Test the Supabase read endpoint with limit parameter."""
    # Mock the Supabase client response
    mock_client = mock.Mock()
    mock_table = mock.Mock()
    mock_select = mock.Mock()
    mock_limit = mock.Mock()
    mock_response = mock.Mock()
    mock_response.data = [{"id": 1, "name": "Test User 1"}]

    # Chain the mock calls
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.limit.return_value = mock_limit
    mock_limit.execute = mock.AsyncMock(return_value=mock_response)

    # Mock acreate_client to return the mock client when awaited
    async def mock_create(url, key):
        return mock_client

    mock_acreate_client.side_effect = mock_create

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

    # Verify limit was called
    mock_select.limit.assert_called_once_with(1)


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
@mock.patch("gen_ai_on_aws.endpoints.endpoints.acreate_client")
def test_supabase_read_query_error(mock_acreate_client, client):
    """Test the Supabase read endpoint when query fails."""
    # Mock the Supabase client to raise an error
    mock_client = mock.Mock()
    mock_table = mock.Mock()
    mock_select = mock.Mock()
    mock_select.execute = mock.AsyncMock(side_effect=Exception("Database connection error"))

    # Chain the mock calls
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select

    # Mock acreate_client to return the mock client when awaited
    async def mock_create(url, key):
        return mock_client

    mock_acreate_client.side_effect = mock_create

    # Test the endpoint
    response = client.post(
        "/endpoints/supabase-read",
        json={"table": "users", "select": "*"},
    )

    # Should return 500 error when query fails
    assert response.status_code == 500
    assert "Failed to read from Supabase" in response.json()["detail"]
