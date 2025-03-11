import unittest.mock as mock
import pytest
from fastapi.testclient import TestClient

from gen_ai_on_aws.main import app
from gen_ai_on_aws.examples.types import User, ExtractUserRequest
from gen_ai_on_aws.services.queue_service import QueueService


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_hello(client):
    """Test the hello endpoint."""
    response = client.get("/examples/hello")
    assert response.status_code == 200
    assert response.json() == "Hello, world!"


def test_extract_user(client):
    """Test the extract user endpoint with valid user data."""
    test_text = (
        "My name is John Doe, I am 30 years old, and my email is john@example.com"
    )
    response = client.post("/examples/extract-user", json={"text": test_text})

    assert response.status_code == 200
    data = response.json()

    user = User.model_validate(data)
    assert user.name == "John Doe"
    assert user.age == 30
    assert user.email == "john@example.com"

    # Test with missing email
    test_text_no_email = "My name is Jane Doe and I am 25 years old"
    response = client.post("/examples/extract-user", json={"text": test_text_no_email})

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
    response = client.post("/examples/extract-user", json={"text": test_text})

    # Since the LLM might try to hallucinate values, we should check that
    # the response at least contains valid User model fields
    assert response.status_code == 200
    data = response.json()
    assert data is None


@mock.patch("gen_ai_on_aws.examples.examples.settings")
@mock.patch.object(QueueService, 'send_message')
def test_extract_user_async(mock_send_message, mock_settings, client):
    """Test the async extract user endpoint."""
    # Set up the settings mock to return a queue URL
    mock_settings.sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
    
    # Set up the send_message mock to return a request ID
    mock_send_message.return_value = "test-request-id-123"
    
    # Test the endpoint
    test_text = "My name is John Doe, I am 30 years old, and my email is john@example.com"
    response = client.post("/examples/extract-user-async", json={"text": test_text})
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["request_id"] == "test-request-id-123"
    
    # Verify the queue service was called correctly
    mock_send_message.assert_called_once()