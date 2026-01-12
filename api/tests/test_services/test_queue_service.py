import unittest.mock as mock

import pytest

from gen_ai_on_aws.endpoints.types import ExtractUserRequest
from gen_ai_on_aws.services.queue_service import QueueService


@pytest.fixture
def queue_service():
    """Return a QueueService with a mock SQS client."""
    service = QueueService(queue_url="https://sqs.us-east-1.amazonaws.com/123456789012/test-queue")
    # Mock the SQS client
    service.sqs_client = mock.MagicMock()
    return service


def test_send_message(queue_service):
    """Test sending a message to the queue."""
    # Mock the SQS client response
    queue_service.sqs_client.send_message.return_value = {"MessageId": "test-message-id-123"}

    # Create a test request
    request = ExtractUserRequest(text="This is a test text")

    # Call the send_message method
    request_id = queue_service.send_message(request)

    # Verify the result
    assert request_id is not None

    # Verify the SQS client was called correctly
    queue_service.sqs_client.send_message.assert_called_once()
    call_args = queue_service.sqs_client.send_message.call_args[1]
    assert call_args["QueueUrl"] == "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"
    assert "MessageBody" in call_args


def test_send_message_failure(queue_service):
    """Test handling failure when sending a message to the queue."""
    # Mock the SQS client to raise an exception
    queue_service.sqs_client.send_message.side_effect = Exception("Test error")

    # Create a test request
    request = ExtractUserRequest(text="This is a test text")

    # Call the send_message method
    request_id = queue_service.send_message(request)

    # Verify the result
    assert request_id is None

    # Verify the SQS client was called
    queue_service.sqs_client.send_message.assert_called_once()
