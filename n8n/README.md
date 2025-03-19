# n8n-utils

Command-line utility for managing n8n workflows and deployments.

## Installation

Install using uv:

```bash
uv sync
```

## Usage

The n8n-utils CLI tool helps you manage n8n workflows:

```bash
# Import/update a workflow using a template
n8n-utils --workflow-template-path templates/job_opportunities.json --server-url 'http://localhost:5678' --n8n-api-key "$LOCAL_N8N_API_KEY"
```

Parameters:
- `--workflow-template-path`: Path to the workflow template file
- `--server-url`: URL of the n8n server
- `--n8n-api-key`: API key for the n8n server (environment variable recommended)
- `--template-values`: Optional JSON string of template values

## Features

- Import new workflows to n8n
- Update existing workflows
- Template-based workflow definitions with variable substitution
- Automated workflow deployment

## Development

```bash
# Run tests
pytest

# Run tests with verbose output
pytest -v
```