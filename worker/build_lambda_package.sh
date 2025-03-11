#!/usr/bin/env bash
set -e

# Determine the script directory and switch to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INITIAL_DIR="$(pwd)"

# Check if running from repo root or worker directory
if [[ "$INITIAL_DIR" == "$REPO_ROOT" ]]; then
    # Running from repo root
    cd "$SCRIPT_DIR"
    RELATIVE_PATH="worker/"
else
    # Running from within worker directory
    RELATIVE_PATH="./"
fi

# https://docs.astral.sh/uv/guides/integration/aws-lambda/#deploying-a-zip-archive
SHORT_SHA=$(git rev-parse --short HEAD)

# Check if there are any changes in the current directory
if git status --porcelain . | grep -q .; then
    # Append _SNAPSHOT suffix if changes are detected
    SHORT_SHA="${SHORT_SHA}-SNAPSHOT"
fi

# Create version.py with current version
mkdir -p worker
echo "VERSION = \"${SHORT_SHA}\"" > worker/version.py

# Create build directories
mkdir -p build/packages

uv export --frozen --no-dev --no-editable -o "build/requirements-${SHORT_SHA}.txt"
uv pip install \
   --no-installer-metadata \
   --no-compile-bytecode \
   --python-platform x86_64-manylinux2014 \
   --python 3.13 \
   --target "build/packages/${SHORT_SHA}" \
   -r "build/requirements-${SHORT_SHA}.txt"

# Following the AWS Lambda documentation, we can then bundle these dependencies into a zip as follows:
cd "build/packages/${SHORT_SHA}"
zip -qr ../worker-package-${SHORT_SHA}.zip .
cd ../../..

# Finally, we can add the application code to the zip archive:
zip -qr build/packages/worker-package-${SHORT_SHA}.zip worker

# Clean up the temporary version file
rm worker/version.py

echo "Package created at: ${RELATIVE_PATH}build/packages/worker-package-${SHORT_SHA}.zip"

# Return to the original directory
cd "$INITIAL_DIR"