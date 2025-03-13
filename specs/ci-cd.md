# CI/CD setup

## Overview

We want to setup a CI/CD pipeline for the project, using GitHub Actions.

## Implementation details

We want to use the GitHub Actions to build the project, and then deploy the project to AWS.

Things I want to check:

 - run ruff, and other tools that are used by pre-commit hooks
 - run api unit tests (cd api, and "uv run pytest")
 - try to locally start the API (cd api, and "uv run fastapi run gen_ai_on_aws/main.py --reload")
 - run worker unit tests (cd worker, and "uv run pytest")
 - check pulumi scripts by simulating creation of an empty stack (cd provisioning, ...)
 - build the project (./build_lambda_packages.sh)
 - do not deploy yet

Things to consider:
 - need OIDC provider for AWS so we can deploy from GitHub Actions, and access secrets
 - need to create a new IAM role for the GitHub Actions runner
 - need branches to deploy to different stages (dev, demo) (demo is prod)
 - need to setup a build badge
 - need a code coverage badge as well (integration with codecov.io)

