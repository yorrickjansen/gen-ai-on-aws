#!/bin/bash
set -e

file_path=$(jq -r '.tool_input.file_path')

# Only process Python files
if [[ "$file_path" =~ \.py$ ]]; then
  echo "Running checks on $file_path..."

  # Get the project root directory (where this script is located)
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

  # Determine which directory to run from (api vs provisioning)
  if [[ "$file_path" =~ ^api/ ]]; then
    cd "$SCRIPT_DIR/api"
    relative_path="${file_path#api/}"
    echo "  Formatting with ruff..."
    uv run ruff format "$relative_path" 2>&1 || true
    echo "  Linting with ruff..."
    uv run ruff check --fix "$relative_path" 2>&1 || true
    echo "  Type checking with pyright..."
    uv run pyright "$relative_path" 2>&1 || true
  elif [[ "$file_path" =~ ^provisioning/ ]]; then
    cd "$SCRIPT_DIR/provisioning"
    relative_path="${file_path#provisioning/}"
    echo "  Formatting with ruff..."
    uv run ruff format "$relative_path" 2>&1 || true
    echo "  Linting with ruff..."
    uv run ruff check --fix "$relative_path" 2>&1 || true
    echo "  Type checking with pyright..."
    uv run pyright "$relative_path" 2>&1 || true
  fi

  echo "✓ Checks complete for $file_path"
fi
