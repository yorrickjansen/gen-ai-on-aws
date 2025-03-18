"""Tests for the CLI interface."""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from n8n.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


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


def test_import_workflow_new(runner, mock_template_file):
    """Test importing a new workflow."""
    with patch("n8n.main.get_workflow_by_name", return_value=None) as mock_get:
        with patch("n8n.main.create_workflow") as mock_create:
            mock_create.return_value = {"id": "new-id", "name": "test-workflow"}

            # Run the command
            result = runner.invoke(
                app,
                [
                    "import-workflow",
                    "--workflow-template-path",
                    mock_template_file,
                    "--server-url",
                    "http://localhost:5678",
                    "--n8n-api-key",
                    "api-key",
                    "--template-values",
                    '{"service_credentials_id": "1234567890"}',
                ],
            )

            # Check that the command ran successfully
            assert result.exit_code == 0
            assert "Creating new workflow: test-workflow" in result.stdout
            assert "Workflow created successfully" in result.stdout

            # Verify the right function was called
            mock_get.assert_called_once()
            mock_create.assert_called_once()


def test_import_workflow_update(runner, mock_template_file):
    """Test updating an existing workflow."""
    with patch("n8n.main.get_workflow_by_name") as mock_get:
        mock_get.return_value = {"id": "abc123", "name": "test-workflow"}

        with patch("n8n.main.update_workflow") as mock_update:
            mock_update.return_value = {"id": "abc123", "name": "test-workflow"}

            # Run the command
            result = runner.invoke(
                app,
                [
                    "import-workflow",
                    "--workflow-template-path",
                    mock_template_file,
                    "--server-url",
                    "http://localhost:5678",
                    "--n8n-api-key",
                    "api-key",
                    "--template-values",
                    '{"service_credentials_id": "1234567890"}',
                ],
            )

            # Check that the command ran successfully
            assert result.exit_code == 0
            assert "Updating existing workflow: test-workflow" in result.stdout
            assert "Workflow updated successfully" in result.stdout

            # Verify the right functions were called
            mock_get.assert_called_once()
            mock_update.assert_called_once()


def test_import_workflow_invalid_template_values(runner, mock_template_file):
    """Test importing a workflow with invalid template values."""
    # Run the command with invalid template values
    result = runner.invoke(
        app,
        [
            "import-workflow",
            "--workflow-template-path",
            mock_template_file,
            "--server-url",
            "http://localhost:5678",
            "--n8n-api-key",
            "api-key",
            "--template-values",
            "invalid json",
        ],
    )

    # Check that the command failed
    assert result.exit_code == 1
    assert "Error: template-values must be a valid JSON string" in result.stdout


def test_import_workflow_nonexistent_template(runner):
    """Test importing a workflow with a nonexistent template file."""
    # Run the command with a nonexistent template file
    result = runner.invoke(
        app,
        [
            "import-workflow",
            "--workflow-template-path",
            "/nonexistent/path.json",
            "--server-url",
            "http://localhost:5678",
            "--n8n-api-key",
            "api-key",
            "--template-values",
            "{}",
        ],
    )

    # Check that the command failed
    assert result.exit_code == 1
    assert "Error: Template file /nonexistent/path.json not found" in result.stdout
