#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Read version from command line or set default
VERSION="${1:-$(date +%Y%m%d%H%M%S)}"
echo "Building Lambda package with version: $VERSION"

# Create build directory if it doesn't exist
mkdir -p build/packages

# Create a temporary directory for building
BUILD_DIR=$(mktemp -d)
echo "Using temporary directory: $BUILD_DIR"

# Install dependencies and worker package
cd "$BUILD_DIR"
uv pip install --target . -r "$SCRIPT_DIR/pyproject.toml"

# Copy source code
cp -r "$SCRIPT_DIR/worker" "$BUILD_DIR/worker"

# Create version.py
echo "VERSION = \"$VERSION\"" > "$BUILD_DIR/worker/version.py"

# Create zip file
cd "$BUILD_DIR"
zip -r "$SCRIPT_DIR/build/packages/worker-package-$VERSION.zip" .

# Clean up
rm -rf "$BUILD_DIR"

echo "Package created at: $SCRIPT_DIR/build/packages/worker-package-$VERSION.zip"