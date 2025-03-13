#!/bin/bash
set -e

# Run Pulumi commands from repo root
cd "$(dirname "$0")/provisioning"

# Pass all arguments to pulumi
uv run pulumi "$@"