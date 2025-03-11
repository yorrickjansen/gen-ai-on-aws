import os
import pytest

@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for testing."""
    os.environ["STACK_NAME"] = "test-stack"
    os.environ["MODEL"] = "test-model"
    os.environ["FASTAPI_DEBUG"] = "true"
    os.environ["SQS_QUEUE_URL"] = "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"