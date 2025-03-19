"""Common fixtures for tests."""

import json
import os
import tempfile

import pytest


@pytest.fixture
def mock_template_file():
    """Create a temporary template file for testing."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        template_content = json.dumps(
            {
                "name": "test-workflow",
                "credentials": {
                    "service": {
                        "id": "{{ service_credentials_id }}",
                        "name": "Service account",
                    }
                },
            }
        )
        tmp.write(template_content)
        template_path = tmp.name

    yield template_path

    # Clean up the temporary file
    os.unlink(template_path)


@pytest.fixture
def mock_template_with_missing_name():
    """Create a temporary template file without a name field."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        template_content = json.dumps(
            {
                "credentials": {
                    "service": {
                        "id": "12345",  # Not using a template variable
                        "name": "Service account",
                    }
                },
            }
        )
        tmp.write(template_content)
        template_path = tmp.name

    yield template_path

    # Clean up the temporary file
    os.unlink(template_path)


@pytest.fixture
def mock_invalid_json_template():
    """Create a temporary template file with invalid JSON."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        # Valid Jinja2 template but produces invalid JSON
        tmp.write('{ "name": "test-workflow", "invalid": }')
        template_path = tmp.name

    yield template_path

    # Clean up the temporary file
    os.unlink(template_path)


@pytest.fixture
def mock_template_with_variables():
    """Create a template file with variables but no Jinja2 syntax errors."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        template_content = json.dumps(
            {
                "name": "test-workflow",
                "credentials": {
                    "service": {
                        "id": "{{ service_credentials_id }}",
                        "name": "Service account",
                    }
                },
            }
        )
        tmp.write(template_content)
        template_path = tmp.name

    yield template_path

    # Clean up the temporary file
    os.unlink(template_path)


@pytest.fixture
def workflow_data():
    """Workflow data for testing."""
    return {
        "id": "abc123",
        "name": "test-workflow",
        "active": False,
        "nodes": [
            {
                "id": "node1",
                "name": "Start",
                "type": "n8n-nodes-base.start",
                "position": [100, 300],
            }
        ],
        "connections": {},
    }
