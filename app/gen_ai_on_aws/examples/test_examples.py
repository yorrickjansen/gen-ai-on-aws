from fastapi.testclient import TestClient
import unittest.mock as mock
import os

from gen_ai_on_aws.main import app
from gen_ai_on_aws.examples.types import User
from gen_ai_on_aws.services.queue_service import QueueService
from gen_ai_on_aws.config import settings


client = TestClient(app)


def test_hello():
    response = client.get("/examples/hello")
    assert response.status_code == 200
    assert response.json() == "Hello, world!"


def test_extract_user():
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


def test_extract_user_failure():
    # Test with text that doesn't contain any user information
    test_text = "This is a random text without any user information"
    response = client.post("/examples/extract-user", json={"text": test_text})

    # Since the LLM might try to hallucinate values, we should check that
    # the response at least contains valid User model fields
    assert response.status_code == 200
    data = response.json()
    assert data is None


@mock.patch.object(QueueService, 'send_message')
def test_extract_user_async(mock_send_message):
    # Set up a mock SQS queue URL for testing
    original_queue_url = settings.sqs_queue_url
    settings.sqs_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
    
    try:
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
    finally:
        # Restore the original queue URL setting
        settings.sqs_queue_url = original_queue_url
