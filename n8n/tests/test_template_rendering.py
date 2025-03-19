"""Tests for the template rendering functionality."""

import json
import os
import tempfile

import jinja2
import pytest

from n8n.main import render_template


def test_render_template(mock_template_file):
    """Test rendering a template with values."""
    # Define template values
    template_values = {"service_credentials_id": "1234567890"}

    # Render the template
    rendered = render_template(mock_template_file, template_values)

    # Parse the rendered template as JSON
    workflow_data = json.loads(rendered)

    # Check that the template was rendered correctly
    assert workflow_data["name"] == "test-workflow"
    assert workflow_data["credentials"]["service"]["id"] == "1234567890"
    assert workflow_data["credentials"]["service"]["name"] == "Service account"


def test_render_template_with_missing_variables_fails():
    """Test that rendering fails when template variables are missing."""
    # Create a simple template file
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        tmp.write('{"name": "test-{{ value }}"}')
        template_path = tmp.name

    try:
        # Render the template with empty values - should raise an exception
        with pytest.raises(jinja2.exceptions.UndefinedError) as excinfo:
            render_template(template_path, {})

        # Check the error message indicates the missing variable
        assert "'value' is undefined" in str(excinfo.value)
    finally:
        # Clean up the temporary file
        os.unlink(template_path)


def test_render_template_with_incorrect_variable_name_fails():
    """Test that rendering fails when using incorrect variable names."""
    # Create a template file with a variable
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        tmp.write('{"name": "test-{{ value }}"}')
        template_path = tmp.name

    try:
        # Render the template with a different variable name - should raise an exception
        with pytest.raises(jinja2.exceptions.UndefinedError) as excinfo:
            render_template(template_path, {"other_value": "test"})

        # Check the error message indicates the missing variable
        assert "'value' is undefined" in str(excinfo.value)
    finally:
        # Clean up the temporary file
        os.unlink(template_path)


def test_render_template_with_complex_values():
    """Test rendering a template with complex values."""
    # Create a template file with nested values
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp:
        template_content = json.dumps(
            {
                "name": "test-workflow",
                "nodes": [
                    {
                        "id": "{{ node_id }}",
                        "parameters": {
                            "values": {
                                "string": [
                                    {
                                        "name": "{{ param_name }}",
                                        "value": "{{ param_value }}",
                                    }
                                ]
                            }
                        },
                    }
                ],
            }
        )
        tmp.write(template_content)
        template_path = tmp.name

    try:
        # Define template values
        template_values = {
            "node_id": "abc123",
            "param_name": "test-param",
            "param_value": "test-value",
        }

        # Render the template
        rendered = render_template(template_path, template_values)

        # Parse the rendered template as JSON
        workflow_data = json.loads(rendered)

        # Check that the template was rendered correctly
        assert workflow_data["name"] == "test-workflow"
        assert workflow_data["nodes"][0]["id"] == "abc123"
        assert (
            workflow_data["nodes"][0]["parameters"]["values"]["string"][0]["name"]
            == "test-param"
        )
        assert (
            workflow_data["nodes"][0]["parameters"]["values"]["string"][0]["value"]
            == "test-value"
        )
    finally:
        # Clean up the temporary file
        os.unlink(template_path)


def test_render_template_file_not_found():
    """Test rendering a template that doesn't exist."""
    # Try to render a nonexistent template
    with pytest.raises(FileNotFoundError) as excinfo:
        render_template("/nonexistent/path.json", {})

    # Check the error message
    assert "Template file not found" in str(excinfo.value)
