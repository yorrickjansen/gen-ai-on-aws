"""Lambda layer management with hash-based versioning."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pulumi


def get_uv_lock_hash(lock_file_path: str) -> str:
    """Calculate hash from uv.lock file to determine layer version.

    Args:
        lock_file_path: Path to the uv.lock file

    Returns:
        First 12 characters of SHA256 hash of the lock file
    """
    return hashlib.sha256(Path(lock_file_path).read_bytes()).hexdigest()[:12]


def layer_exists_in_aws(layer_name: str) -> str | None:
    """Check if a Lambda layer exists in AWS.

    Args:
        layer_name: Name of the Lambda layer to check

    Returns:
        Layer version ARN if it exists, None otherwise
    """
    result = subprocess.run(
        ["aws", "lambda", "list-layer-versions", "--layer-name", layer_name],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        versions = data.get("LayerVersions", [])
        return versions[0]["LayerVersionArn"] if versions else None
    return None


def publish_layer_via_cli(
    layer_name: str, layer_zip_path: str, compatible_runtimes: list[str] | None = None
) -> str:
    """Publish a new Lambda layer version using AWS CLI.

    Args:
        layer_name: Name of the layer
        layer_zip_path: Path to the layer zip file
        compatible_runtimes: List of compatible Lambda runtimes

    Returns:
        Layer version ARN
    """
    if compatible_runtimes is None:
        compatible_runtimes = ["python3.13"]

    result = subprocess.run(
        [
            "aws",
            "lambda",
            "publish-layer-version",
            "--layer-name",
            layer_name,
            "--zip-file",
            f"fileb://{layer_zip_path}",
            "--compatible-runtimes",
            *compatible_runtimes,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)
    return data["LayerVersionArn"]


def get_or_create_layer(
    name: str,
    deps_hash: str,
    layer_zip_path: str,
    description: str = "",
    compatible_runtimes: list[str] | None = None,
) -> str:
    """Get existing Lambda layer or create a new one.

    This function checks if a layer with the given hash-based name exists in AWS.
    If it exists, it returns the ARN. If not, it publishes a new layer version.

    Note: Layers are NOT managed as Pulumi resources to avoid state conflicts.
    They are created directly via AWS CLI when needed.

    Args:
        name: Base name for the layer (e.g., "api" or "worker")
        deps_hash: Hash of the dependencies (from uv.lock)
        layer_zip_path: Path to the layer zip file
        description: Description for the layer
        compatible_runtimes: List of compatible Lambda runtimes

    Returns:
        Layer version ARN (either existing or newly created)
    """
    if compatible_runtimes is None:
        compatible_runtimes = ["python3.13"]

    layer_name = f"{deps_hash}-{name}-libs"

    pulumi.log.info(f"Layer name: {layer_name}")

    # Check if layer exists in AWS
    existing_layer_arn = layer_exists_in_aws(layer_name)

    if existing_layer_arn:
        # Layer already published in AWS - reuse it
        pulumi.log.info(f"✓ Reusing existing {name} layer: {existing_layer_arn}")
        return existing_layer_arn
    else:
        # Layer doesn't exist - publish it using AWS CLI (not Pulumi resource)
        pulumi.log.info(f"Publishing new {name} layer from {layer_zip_path}")
        layer_arn = publish_layer_via_cli(
            layer_name, layer_zip_path, compatible_runtimes
        )
        pulumi.log.info(f"✓ Published {name} layer: {layer_arn}")
        return layer_arn


def get_layer_for_lambda(
    name: str, lock_file_path: str, build_dir: str = "build/layers"
) -> str:
    """Get the Lambda layer ARN for a given component.

    This is a convenience function that:
    1. Calculates the hash from the uv.lock file
    2. Determines the layer zip path
    3. Calls get_or_create_layer to get or create the layer

    Args:
        name: Component name (e.g., "api" or "worker")
        lock_file_path: Path to the uv.lock file (relative to project root)
        build_dir: Directory where layer zips are stored (relative to component)

    Returns:
        Layer version ARN
    """
    # Calculate hash from uv.lock
    deps_hash = get_uv_lock_hash(lock_file_path)

    # Determine layer zip path
    layer_name = f"{deps_hash}-{name}-libs"
    layer_zip_path = f"{os.path.dirname(lock_file_path)}/{build_dir}/{layer_name}.zip"

    # Get or create the layer
    return get_or_create_layer(
        name=name,
        deps_hash=deps_hash,
        layer_zip_path=layer_zip_path,
        description=f"{name.capitalize()} dependencies (hash: {deps_hash})",
    )
