"""CLI tool to help with the management of n8n workflows."""

import json
import os
from pathlib import Path
from typing import Annotated, Dict, Optional

import jinja2
import requests
import typer

app = typer.Typer(help="CLI tool to help with the management of n8n workflows.")


def render_template(template_path: str, template_values: Dict[str, str]) -> str:
    """Render a Jinja2 template with the given values."""
    template_dir = os.path.dirname(template_path)
    template_file = os.path.basename(template_path)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    template = env.get_template(template_file)

    return template.render(**template_values)


def get_workflow_by_name(
    server_url: str, n8n_api_key: str, workflow_name: str
) -> Optional[Dict]:
    """Get a workflow from n8n by name."""
    headers = {"X-N8N-API-KEY": n8n_api_key, "Accept": "application/json"}

    response = requests.get(
        f"{server_url}/api/v1/workflows",
        headers=headers,
        params={"name": workflow_name},
    )

    if response.status_code == 200:
        workflows = response.json()
        if workflows and len(workflows["data"]) > 0:
            return workflows["data"][0]

    return None


def create_workflow(server_url: str, n8n_api_key: str, workflow_data: Dict) -> Dict:
    """Create a new workflow in n8n."""
    headers = {
        "X-N8N-API-KEY": n8n_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{server_url}/api/v1/workflows", headers=headers, json=workflow_data
    )

    response.raise_for_status()
    return response.json()


def update_workflow(
    server_url: str, n8n_api_key: str, workflow_id: str, workflow_data: Dict
) -> Dict:
    """Update an existing workflow in n8n."""
    headers = {
        "X-N8N-API-KEY": n8n_api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.put(
        f"{server_url}/api/v1/workflows/{workflow_id}",
        headers=headers,
        json=workflow_data,
    )

    response.raise_for_status()
    return response.json()


@app.command()
def import_workflow(
    workflow_template_path: Annotated[
        str,
        typer.Option(
            "--workflow-template-path", help="Path to the workflow template file"
        ),
    ],
    server_url: Annotated[
        str, typer.Option("--server-url", help="URL of the n8n server")
    ],
    n8n_api_key: Annotated[
        str, typer.Option("--n8n-api-key", help="API key for the n8n server")
    ],
    template_values: Annotated[
        str, typer.Option("--template-values", help="JSON string of template values")
    ] = "{}",
):
    """Import a workflow template into n8n.

    This command will:
    1. Check if a workflow with the same name already exists in n8n
    2. If it exists, update it with the rendered template
    3. If it doesn't exist, create a new workflow using the rendered template
    """
    # Convert template_values from JSON string to dict
    try:
        values = json.loads(template_values)
    except json.JSONDecodeError:
        typer.echo("Error: template-values must be a valid JSON string")
        raise typer.Exit(code=1)

    # Check if template file exists
    template_path = Path(workflow_template_path)
    if not template_path.exists():
        typer.echo(f"Error: Template file {workflow_template_path} not found")
        raise typer.Exit(code=1)

    # Render the template
    try:
        rendered_template = render_template(str(template_path), values)
    except Exception as e:
        typer.echo(f"Error rendering template: {str(e)}")
        raise typer.Exit(code=1)

    # Parse the rendered template as JSON
    try:
        workflow_data = json.loads(rendered_template)
    except json.JSONDecodeError:
        typer.echo("Error: Failed to parse rendered template as JSON")
        raise typer.Exit(code=1)

    # Get the workflow name from the template
    workflow_name = workflow_data.get("name")
    if not workflow_name:
        typer.echo("Error: Workflow template must contain a 'name' field")
        raise typer.Exit(code=1)

    # Check if workflow exists in n8n
    existing_workflow = get_workflow_by_name(server_url, n8n_api_key, workflow_name)

    # Create or update the workflow
    try:
        if existing_workflow:
            typer.echo(f"Updating existing workflow: {workflow_name}")
            result = update_workflow(
                server_url, n8n_api_key, existing_workflow["id"], workflow_data
            )
            typer.echo(f"Workflow updated successfully (ID: {result['id']})")
        else:
            typer.echo(f"Creating new workflow: {workflow_name}")
            result = create_workflow(server_url, n8n_api_key, workflow_data)
            typer.echo(f"Workflow created successfully (ID: {result['id']})")
    except requests.RequestException as e:
        typer.echo(f"Error communicating with n8n server: {str(e)}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
