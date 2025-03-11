# CLAUDE.md - Gen-AI-on-AWS Codebase Guidelines

## Project Structure
- `/app`: FastAPI application code
- `/provisioning`: Pulumi infrastructure code

## Development Environment
- Python >=3.13 for app, >=3.12 for provisioning
- Uses uv for package management

## Build & Deployment
- Run `app/build_lambda_package.sh` to create Lambda zip package

## Testing
- Framework: pytest with pytest-asyncio
- Run tests: `pytest` or `pytest app/gen_ai_on_aws/examples/test_examples.py`
- Single test: `pytest app/gen_ai_on_aws/examples/test_examples.py::test_hello`

## Code Style
- Format: Ruff (with Black profile)
- Linting: Ruff
- Import sorting: isort with Black profile
- Pre-commit hooks configured for automation
- Type annotations used extensively

## Conventions
- Descriptive function names (snake_case)
- Explicit error handling (usually returning None for failures)
- Type annotations for function parameters and return values
- Route organization: Uses FastAPI routers for structure
- Logging via standard Python logging module