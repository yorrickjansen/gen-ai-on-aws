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
    request = ExtractUserRequest(
        text="This is a random text without any user information"
    )

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


def test_lambda_handler_sqs():
    """Test the Lambda handler function with SQS event."""
    import asyncio

    from worker.main import lambda_handler

    # We need to mock the process_message function, not asyncio.run directly
    with mock.patch("worker.main.process_message") as mock_process:
        # Create a mock coroutine that will be awaited by asyncio.run
        mock_coro = mock.MagicMock()
        mock_coro.__await__ = lambda: (yield from asyncio.sleep(0).__await__())
        mock_process.return_value = mock_coro
        # Set the result that will be returned when the coroutine is awaited
        asyncio.run = mock.MagicMock(
            return_value={
                "request_id": "test-id",
                "result": {"name": "John Doe", "age": 30, "email": "john@example.com"},
                "success": True,
            }
        )

        # Create a test SQS event
        event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "request_id": "test-id",
                            "payload": {
                                "text": "My name is John Doe, I am 30 years old, and my email is john@example.com"
                            },
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

        # Verify process_message was called with the correct parameters
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0][0]
        # Convert string back to dict for comparison
        called_with = json.loads(call_args)
        expected = {
            "request_id": "test-id",
            "payload": {
                "text": "My name is John Doe, I am 30 years old, and my email is john@example.com"
            },
        }
        assert called_with == expected


def test_lambda_handler_direct_n8n():
    """Test the Lambda handler function with direct n8n invocation."""
    import asyncio

    from worker.main import lambda_handler

    # We need to mock the process_message function, not asyncio.run directly
    with mock.patch("worker.main.process_message") as mock_process:
        # Create a mock coroutine that will be awaited by asyncio.run
        mock_coro = mock.MagicMock()
        mock_coro.__await__ = lambda: (yield from asyncio.sleep(0).__await__())
        mock_process.return_value = mock_coro
        # Set the result that will be returned when the coroutine is awaited
        asyncio.run = mock.MagicMock(
            return_value={
                "request_id": "n8n-request-123",
                "result": {"name": "Bob", "age": 41},
                "success": True,
            }
        )

        # Create a test direct n8n event
        event = {
            "request_id": "n8n-request-123",
            "payload": {"text": "hello my name is bob 41 yo"},
        }

        # Process the event
        result = lambda_handler(event, None)

        # Verify the result
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "results" in body
        assert len(body["results"]) == 1
        assert body["results"][0]["success"] is True

        # Verify process_message was called with the correct parameters
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0][0]
        # Convert string back to dict for comparison
        called_with = json.loads(call_args)
        expected = {
            "request_id": "n8n-request-123",
            "payload": {"text": "hello my name is bob 41 yo"},
        }
        assert called_with == expected
