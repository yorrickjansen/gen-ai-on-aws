"""Tests for the n8n workflow API functions."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from n8n.main import create_workflow, get_workflow_by_name, update_workflow


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock()
    response.status_code = 200
    return response


def test_get_workflow_by_name(mock_response):
    """Test getting a workflow by name."""
    # Mock the response data
    mock_response.json.return_value = {
        "data": [
            {
                "id": "abc123",
                "name": "test-workflow",
            }
        ]
    }

    # Patch the requests.get method
    with patch("requests.get", return_value=mock_response) as mock_get:
        # Call the function
        result = get_workflow_by_name(
            "http://localhost:5678", "api-key", "test-workflow"
        )

        # Check that the function called the API correctly
        mock_get.assert_called_once_with(
            "http://localhost:5678/api/v1/workflows",
            headers={"X-N8N-API-KEY": "api-key", "Accept": "application/json"},
            params={"name": "test-workflow"},
        )

        # Check that the function returned the correct data
        assert result == {"id": "abc123", "name": "test-workflow"}


def test_get_workflow_by_name_not_found(mock_response):
    """Test getting a workflow that doesn't exist."""
    # Mock the response data with empty results
    mock_response.json.return_value = {"data": []}

    # Patch the requests.get method
    with patch("requests.get", return_value=mock_response) as mock_get:
        # Call the function
        result = get_workflow_by_name(
            "http://localhost:5678", "api-key", "nonexistent-workflow"
        )

        # Check that the function called the API correctly
        mock_get.assert_called_once_with(
            "http://localhost:5678/api/v1/workflows",
            headers={"X-N8N-API-KEY": "api-key", "Accept": "application/json"},
            params={"name": "nonexistent-workflow"},
        )

        # Check that the function returned None
        assert result is None


def test_get_workflow_by_name_error():
    """Test getting a workflow when the API returns an error."""
    # Create a mock response with an error status code
    error_response = MagicMock()
    error_response.status_code = 500

    # Patch the requests.get method
    with patch("requests.get", return_value=error_response) as mock_get:
        # Call the function
        result = get_workflow_by_name(
            "http://localhost:5678", "api-key", "test-workflow"
        )

        # Check that the function called the API correctly
        mock_get.assert_called_once_with(
            "http://localhost:5678/api/v1/workflows",
            headers={"X-N8N-API-KEY": "api-key", "Accept": "application/json"},
            params={"name": "test-workflow"},
        )

        # Check that the function returned None
        assert result is None


def test_create_workflow(mock_response, workflow_data):
    """Test creating a new workflow."""
    # Mock the response data
    mock_response.json.return_value = workflow_data

    # Patch the requests.post method
    with patch("requests.post", return_value=mock_response) as mock_post:
        # Call the function
        result = create_workflow("http://localhost:5678", "api-key", workflow_data)

        # Check that the function called the API correctly
        mock_post.assert_called_once_with(
            "http://localhost:5678/api/v1/workflows",
            headers={
                "X-N8N-API-KEY": "api-key",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=workflow_data,
        )

        # Check that the function returned the correct data
        assert result == workflow_data


def test_create_workflow_error(workflow_data):
    """Test creating a workflow when the API returns an error."""
    # Patch the requests.post method to raise an exception
    with patch(
        "requests.post", side_effect=requests.RequestException("API error")
    ) as mock_post:
        # Call the function with assertRaises
        with pytest.raises(requests.RequestException) as excinfo:
            create_workflow("http://localhost:5678", "api-key", workflow_data)

        # Check that the exception message is correct
        assert "API error" in str(excinfo.value)

        # Check that the function called the API correctly
        mock_post.assert_called_once_with(
            "http://localhost:5678/api/v1/workflows",
            headers={
                "X-N8N-API-KEY": "api-key",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=workflow_data,
        )


def test_update_workflow(mock_response, workflow_data):
    """Test updating an existing workflow."""
    # Mock the response data
    mock_response.json.return_value = workflow_data

    # Patch the requests.put method
    with patch("requests.put", return_value=mock_response) as mock_put:
        # Call the function
        result = update_workflow(
            "http://localhost:5678", "api-key", "abc123", workflow_data
        )

        # Check that the function called the API correctly
        mock_put.assert_called_once_with(
            "http://localhost:5678/api/v1/workflows/abc123",
            headers={
                "X-N8N-API-KEY": "api-key",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=workflow_data,
        )

        # Check that the function returned the correct data
        assert result == workflow_data


def test_update_workflow_error(workflow_data):
    """Test updating a workflow when the API returns an error."""
    # Patch the requests.put method to raise an exception
    with patch(
        "requests.put", side_effect=requests.RequestException("API error")
    ) as mock_put:
        # Call the function with assertRaises
        with pytest.raises(requests.RequestException) as excinfo:
            update_workflow("http://localhost:5678", "api-key", "abc123", workflow_data)

        # Check that the exception message is correct
        assert "API error" in str(excinfo.value)

        # Check that the function called the API correctly
        mock_put.assert_called_once_with(
            "http://localhost:5678/api/v1/workflows/abc123",
            headers={
                "X-N8N-API-KEY": "api-key",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=workflow_data,
        )
