import os
import pytest

@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for testing."""
    os.environ["STACK_NAME"] = "test-stack"
    os.environ["MODEL"] = "test-model"