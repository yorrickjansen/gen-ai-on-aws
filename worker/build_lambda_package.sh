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
mkdir -p build/layers build/packages

# ============================================
# STEP 1: Build Lambda Layer (dependencies only)
# ============================================
# Calculate hash from uv.lock to determine layer name
DEPS_HASH=$(shasum -a 256 uv.lock | cut -d' ' -f1 | cut -c1-12)
LAYER_NAME="${DEPS_HASH}-worker-libs"
LAYER_ZIP="build/layers/${LAYER_NAME}.zip"

echo "Dependencies hash: ${DEPS_HASH}"
echo "Layer name: ${LAYER_NAME}"

# Check if layer already built locally
if [ -f "$LAYER_ZIP" ]; then
    echo "✓ Layer already built locally: ${LAYER_ZIP}"
else
    echo "Building Lambda layer with dependencies..."

    # Use --prefix to create python/lib/pythonX.Y/site-packages/ structure for layers
    uv export --frozen --no-dev --no-editable -o "build/requirements-${DEPS_HASH}.txt"
    uv pip install \
       --no-installer-metadata \
       --no-compile-bytecode \
       --python-platform x86_64-manylinux_2_17 \
       --python 3.13 \
       --prefix "build/layers/${LAYER_NAME}/python" \
       -r "build/requirements-${DEPS_HASH}.txt"

    # Zip the layer
    cd "build/layers/${LAYER_NAME}"
    zip -qr "../${LAYER_NAME}.zip" python/
    cd ../../..

    # Cleanup intermediate files
    rm -rf "build/layers/${LAYER_NAME}"

    echo "✓ Layer built: ${LAYER_ZIP}"
fi

# ============================================
# STEP 2: Build App Package (code only, no dependencies)
# ============================================
echo "Building app package (code only)..."

# Just zip the application code - dependencies are in the layer
zip -qr "build/packages/worker-${SHORT_SHA}.zip" worker

# Clean up the temporary version file
rm worker/version.py

echo "✓ Package created at: ${RELATIVE_PATH}build/packages/worker-${SHORT_SHA}.zip"
echo ""
echo "Summary:"
echo "  Layer:   ${RELATIVE_PATH}${LAYER_ZIP}"
echo "  App:     ${RELATIVE_PATH}build/packages/worker-${SHORT_SHA}.zip"
echo ""

# Return to the original directory
cd "$INITIAL_DIR"