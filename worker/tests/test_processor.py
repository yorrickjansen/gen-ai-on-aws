import json
import unittest.mock as mock

import pytest

from worker.models.queue import ExtractUserRequest, User
from worker.services.processor import Processor


@pytest.fixture
def processor():
    """Return a Processor instance."""
    return Processor()


@mock.patch("worker.services.processor.client.chat.completions.create")
async def test_process_extract_user_request(mock_create, processor):
    """Test processing an extract user request."""
    # Mock the LLM response
    mock_user = User(name="John Doe", age=30, email="john@example.com")
    mock_create.return_value = mock_user

    # Create a test request
    request = ExtractUserRequest(
        text="My name is John Doe, I am 30 years old, and my email is john@example.com"
    )

    # Process the request
    result = await processor.process_extract_user_request(request)

    # Verify the result
    assert result is not None
    assert result.name == "John Doe"
    assert result.age == 30
    assert result.email == "john@example.com"

    # Verify the LLM was called correctly
    mock_create.assert_called_once()


@mock.patch("worker.services.processor.client.chat.completions.create")
async def test_process_extract_user_request_no_user(mock_create, processor):
    """Test processing an extract user request with no user information."""
    # Mock the LLM response
    mock_create.return_value = None

    # Create a test request
    request = ExtractUserRequest(text="This is a random text without any user information")

    # Process the request
    result = await processor.process_extract_user_request(request)

    # Verify the result
    assert result is None

    # Verify the LLM was called correctly
    mock_create.assert_called_once()


@mock.patch("worker.services.processor.client.chat.completions.create")
async def test_process_extract_user_request_error(mock_create, processor):
    """Test handling an error when processing an extract user request."""
    # Mock the LLM to raise an exception
    mock_create.side_effect = Exception("Test error")

    # Create a test request
    request = ExtractUserRequest(
        text="My name is John Doe, I am 30 years old, and my email is john@example.com"
    )

    # Process the request
    result = await processor.process_extract_user_request(request)

    # Verify the result
    assert result is None

    # Verify the LLM was called
    mock_create.assert_called_once()


def test_lambda_handler():
    """Test the Lambda handler function."""
    from worker.main import lambda_handler

    # Mock the asyncio.run function
    with mock.patch("asyncio.run") as mock_run:
        mock_run.return_value = {
            "request_id": "test-id",
            "result": {"name": "John Doe", "age": 30, "email": "john@example.com"},
            "success": True,
        }

        # Create a test event
        test_text = "My name is John Doe, I am 30 years old, and my email is john@example.com"
        event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "request_id": "test-id",
                            "payload": {"text": test_text},
                        }
                    )
                }
            ]
        }

        # Process the event
        result = lambda_handler(event, None)

        # Verify the result
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "results" in body
        assert len(body["results"]) == 1
        assert body["results"][0]["success"] is True

        # Verify asyncio.run was called correctly
        mock_run.assert_called_once()
