"""Tests for the CLI interface."""

from unittest.mock import patch

import pytest
import requests
from typer.testing import CliRunner

from n8n.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_import_workflow_new(runner, mock_template_file):
    """Test importing a new workflow."""
    with patch("n8n.main.get_workflow_by_name", return_value=None) as mock_get:
        with patch("n8n.main.create_workflow") as mock_create:
            mock_create.return_value = {"id": "new-id", "name": "test-workflow"}

            # Run the command
            result = runner.invoke(
                app,
                [
                    "-p",
                    mock_template_file,
                    "-u",
                    "http://localhost:5678",
                    "-k",
                    "api-key",
                    "-t",
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
                    "-p",
                    mock_template_file,
                    "-u",
                    "http://localhost:5678",
                    "-k",
                    "api-key",
                    "-t",
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
            "-p",
            mock_template_file,
            "-u",
            "http://localhost:5678",
            "-k",
            "api-key",
            "-t",
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
            "-p",
            "/nonexistent/path.json",
            "-u",
            "http://localhost:5678",
            "-k",
            "api-key",
            "-t",
            "{}",
        ],
    )

    # Check that the command failed
    assert result.exit_code == 1
    assert "Error: Template file /nonexistent/path.json not found" in result.stdout


def test_import_workflow_template_rendering_error(runner, mock_invalid_json_template):
    """Test importing a workflow with a template that can't be rendered as JSON."""
    result = runner.invoke(
        app,
        [
            "-p",
            mock_invalid_json_template,
            "-u",
            "http://localhost:5678",
            "-k",
            "api-key",
            "-t",
            "{}",
        ],
    )

    # Check that the command failed
    assert result.exit_code == 1
    assert "Error: Failed to parse rendered template as JSON" in result.stdout


def test_import_workflow_missing_name(runner, mock_template_with_missing_name):
    """Test importing a workflow with a template missing the name field."""
    result = runner.invoke(
        app,
        [
            "-p",
            mock_template_with_missing_name,
            "-u",
            "http://localhost:5678",
            "-k",
            "api-key",
            "-t",
            "{}",
        ],
    )

    # Check that the command failed
    assert result.exit_code == 1
    assert "Error: Workflow template must contain a 'name' field" in result.stdout


def test_import_workflow_api_error_create(runner, mock_template_file):
    """Test importing a workflow when the API returns an error during creation."""
    with patch("n8n.main.get_workflow_by_name", return_value=None) as mock_get:
        with patch(
            "n8n.main.create_workflow",
            side_effect=requests.RequestException("API error"),
        ) as mock_create:
            # Run the command
            result = runner.invoke(
                app,
                [
                    "-p",
                    mock_template_file,
                    "-u",
                    "http://localhost:5678",
                    "-k",
                    "api-key",
                    "-t",
                    '{"service_credentials_id": "1234567890"}',
                ],
            )

            # Check that the command failed
            assert result.exit_code == 1
            assert "Error communicating with n8n server: API error" in result.stdout

            # Verify the right function was called
            mock_get.assert_called_once()
            mock_create.assert_called_once()


def test_import_workflow_api_error_update(runner, mock_template_file):
    """Test importing a workflow when the API returns an error during update."""
    with patch("n8n.main.get_workflow_by_name") as mock_get:
        mock_get.return_value = {"id": "abc123", "name": "test-workflow"}

        with patch(
            "n8n.main.update_workflow",
            side_effect=requests.RequestException("API error"),
        ) as mock_update:
            # Run the command
            result = runner.invoke(
                app,
                [
                    "-p",
                    mock_template_file,
                    "-u",
                    "http://localhost:5678",
                    "-k",
                    "api-key",
                    "-t",
                    '{"service_credentials_id": "1234567890"}',
                ],
            )

            # Check that the command failed
            assert result.exit_code == 1
            assert "Error communicating with n8n server: API error" in result.stdout

            # Verify the right functions were called
            mock_get.assert_called_once()
            mock_update.assert_called_once()


def test_import_workflow_missing_template_variables(runner, mock_template_file):
    """Test importing a workflow with missing template variables."""
    # Run the command with empty template values - should fail since variables are required
    result = runner.invoke(
        app,
        [
            "-p",
            mock_template_file,
            "-u",
            "http://localhost:5678",
            "-k",
            "api-key",
            "-t",
            "{}",  # Empty JSON object, missing required variables
        ],
    )

    # Check that the command failed
    assert result.exit_code == 1
    assert "Error rendering template" in result.stdout
    assert "'service_credentials_id' is undefined" in result.stdout
