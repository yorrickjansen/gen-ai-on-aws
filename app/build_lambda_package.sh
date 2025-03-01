#!/usr/bin/env bash

# https://docs.astral.sh/uv/guides/integration/aws-lambda/#deploying-a-zip-archive
SHORT_SHA=$(git rev-parse --short HEAD)

# Check if there are any changes in the current directory
if git status --porcelain . | grep -q .; then
    # Append _SNAPSHOT suffix if changes are detected
    SHORT_SHA="${SHORT_SHA}_SNAPSHOT"
fi


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
zip -r ../package-${SHORT_SHA}.zip .
cd ../../..

# Finally, we can add the application code to the zip archive:
zip -r build/packages/package-${SHORT_SHA}.zip gen_ai_on_aws


echo "Built package: ./build/packages/package-${SHORT_SHA}.zip"
