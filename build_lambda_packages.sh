#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:-$(date +%Y%m%d%H%M%S)}"

echo "Building Lambda packages..."

# Build API package
echo "Building API package..."
"$SCRIPT_DIR/api/build_lambda_package.sh"

# Build Worker package with the same version parameter
echo "Building Worker package..."
"$SCRIPT_DIR/worker/build_lambda_package.sh" "$VERSION"

echo "All packages built successfully!"