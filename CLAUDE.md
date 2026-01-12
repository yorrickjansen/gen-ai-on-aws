# CLAUDE.md - Gen-AI-on-AWS Codebase Guidelines

## Core Principles
- **Never assume missing context.** Ask clarifying questions if the request is ambiguous or incomplete.
- **Never hallucinate libraries or functions.** Only use known, verified Python packages. If unsure, use Perplexity to verify (never use WebSearch).
- **Always use Perplexity for web research.** When you need to look up information, use the Perplexity MCP tool (`mcp__perplexity-ask__perplexity_ask`), not WebSearch or Firecrawl.
- **Never use Firecrawl.** Always use Perplexity (`mcp__perplexity-ask__perplexity_ask`) for fetching web content and documentation.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to do so.
- **CRITICAL: When mentioning known bugs or issues, ALWAYS provide the full GitHub issue URL.** This is non-negotiable and extremely important for transparency and verification.
- **When implementing workarounds for known bugs, add code comments with the issue URL.** This helps future developers understand why specific workarounds exist.
- **CRITICAL: ALWAYS propose potential solutions and wait for explicit confirmation before implementing significant changes.** This includes but is not limited to:
  - Changing Python versions or other core dependencies
  - Modifying build or deployment configurations
  - Changing project structure or architecture
  - Adding or removing major dependencies
  - Any change that could have wide-ranging side effects
  - When in doubt, propose multiple options with trade-offs and wait for user decision

## Code Structure & Modularity
- **Keep files concise.** Never create a file longer than 500 lines of code. If a file approaches this limit, refactor it by splitting it into smaller, focused modules.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports.** Prefer relative imports for modules within the same package.
- **Each module should define its own models, services, and an optional data layer file if it makes sense.**

## Style & Conventions
- **Use Python** as the primary language.
- **Follow PEP8 standards.** Use type hints for all function signatures and variables where appropriate.
- **Code quality tools**: The project uses `ruff` for formatting and linting, and `pyright` for type checking. These tools run automatically via post-edit hooks (configured in `.claude/settings.json`).
- **Use `pydantic` for data validation.** Define Pydantic models in `models.py` files within each relevant package.
- **Use `FastAPI` for APIs** and `SQLAlchemy` or `SQLModel` for the ORM, if applicable.
- **Always use Typer library for cli commands**
- **When implementing cli commands, always add a --json option. Also, for commands that write/update resources, implement --dry-run and --yes**
- **Write Google-style docstrings for every function.**
  ```python
  def example_function(param1: str) -> bool:
      """A brief summary of the function's purpose.

      This section provides a more detailed explanation of the function's
      logic, algorithms, and any side effects.

      Args:
          param1: A description of the first parameter.

      Returns:
          A description of the return value.
      """
      pass
    ```

## Testing & Reliability

### Testing Requirement
**EVERY change MUST be tested - either with unit tests or manual tests. No exceptions.**

- **For application code (Python functions, classes, API routes)**: Write Pytest unit tests
- **For infrastructure, scripts, and tooling**: Use manual testing procedures (see below)
- **Document the test approach**: Either add unit tests or document the manual test procedure in the PR/commit

### Unit Testing
- **Always create Pytest unit tests for new features** (e.g., functions, classes, API routes).
- **Update existing unit tests** whenever the logic they cover is modified.
- **Organize tests in a top-level `/tests` directory** that mirrors the main application's structure.
- **Ensure comprehensive test coverage** for each feature, including at a minimum:
  - One test for the expected, "happy path" use case.
  - One test for a known edge case.
  - One test for an expected failure or error case.
- **Always run the full test suite from the project root** after implementing any change to verify that nothing has broken (e.g., `uv run pytest`).

### Manual Testing Procedures

When unit tests are not practical (build scripts, pre-commit hooks, infrastructure), follow these manual test procedures:

#### Lambda Packaging Scripts (`build_lambda_package.sh`)
```bash
# Test clean build
rm -rf api/build/ && ./api/build_lambda_package.sh

# Test layer caching (should skip layer rebuild)
./api/build_lambda_package.sh

# Test with dependency changes
echo "# test" >> api/uv.lock && ./api/build_lambda_package.sh

# Verify artifacts
ls -lh api/build/packages/
ls -lh api/build/layers/

# Test deployment
cd provisioning && uv run pulumi up -y

# Verify Lambda works
http POST $(pulumi stack output apigatewayv2-http-endpoint)examples/extract-user text="test"
```

#### Pre-commit Hooks (`.github/hooks/`)
```bash
# Install hooks
pre-commit install

# Test with clean diff
echo "safe code" > test_file.py
git add test_file.py
git commit -m "test: safe commit"  # Should pass

# Test with sensitive data (should block)
echo 'API_KEY = "sk-proj-real-looking-key-1234567890"' > test_secret.py
git add test_secret.py
git commit -m "test: should block"  # Should be blocked

# Test with placeholder (should allow)
echo 'API_KEY = "YOUR_API_KEY_HERE"' > test_placeholder.py
git add test_placeholder.py
git commit -m "test: should allow placeholder"  # Should pass

# Clean up test files
git reset HEAD
rm -f test_file.py test_secret.py test_placeholder.py
```

#### Infrastructure Changes (Pulumi)
```bash
# Test infrastructure preview
cd provisioning
uv run pulumi preview

# Test deployment to dev stack
uv run pulumi stack select dev
uv run pulumi up -y

# Verify resources created
aws lambda get-function --function-name $(pulumi stack output lambda_function_name)
aws lambda list-layer-versions --layer-name $(pulumi config get app_version)

# Test rollback capability
uv run pulumi stack export > backup.json
```

#### API Endpoints
```bash
# Start local server
cd api && uv run uvicorn gen_ai_on_aws.main:app --reload

# Test endpoints locally
http POST http://localhost:8000/examples/extract-user text="test data"

# Deploy and test on AWS
cd ../provisioning && uv run pulumi up -y
http POST $(pulumi stack output apigatewayv2-http-endpoint)examples/extract-user text="test data"

# Monitor logs
aws logs tail --follow /aws/lambda/$(pulumi stack output lambda_function_name)
```

## Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code.** Ensure all code is understandable to a mid-level developer.
- **Explain complex logic with inline comments.** Use a `# Reason:` comment to clarify the *why* behind a specific implementation choice, not just the *what*.

## Tooling & Environment
### Git
- **Never use `git push --force`**.
- **Never use `git rebase` or `git reset`**.
- **Do not delete or switch branches** unless instructed.
- **Only commit or create Pull Requests when explicitly asked.**
- When asked to commit, write a meaningful commit message.
- Always push the current branch with `git push origin HEAD`.

### Python Environment (uv)
- Use `uv` for Python version and package management.
- Run `uv sync` to install/update dependencies from the lock file.
- Run `uv add <package>` to add a runtime dependency.
- Run `uv add <package> --group dev` to add a development dependency.
- Run commands within the virtual environment using `uv run <command>`. For example, `uv run pytest`.
- To run the project's main CLI, use the entrypoint: `uv run virtual-receptionist ...` (do NOT use `uv run python cli.py ...`).
- Refer to pyproject.toml for the list of dependencies and their versions, as well as for python version (project.requires-python)
- **CRITICAL: After any dependency changes (uv add, uv remove, or manual pyproject.toml edits), ALWAYS test that Lambda packaging still works by running `./api/build_lambda_package.sh` or `./worker/build_lambda_package.sh`**. This ensures all dependencies have compatible wheels for the Lambda Linux x86_64 environment.

### Logging
- **ALWAYS use `loguru` for logging - NEVER use Python's standard `logging` module.**
  - Import: `from loguru import logger`
  - DO NOT use: `import logging` or `logger = logging.getLogger(__name__)`
  - This applies to ALL Python files in both API and Worker directories
- **Configure logging to output in a structured (JSON) format.**
- **Add relevant context to the logger** whenever possible (e.g., request ID, user ID) to simplify debugging and tracing.

### HTTP Calls
- **Always use `httpie`** for making HTTP calls from the terminal (e.g., `http GET ...`).

### Secrets Management

The application uses **environment-based secrets management**:

**Local Development (`.env` file)**:
- Create an `api/.env` file with direct API keys:
  ```env
  ANTHROPIC_API_KEY=sk-ant-xxx
  LANGFUSE_PUBLIC_KEY=pk-xxx
  LANGFUSE_SECRET_KEY=sk-xxx
  STACK_NAME=dev
  ```
- Secrets are loaded directly from the `.env` file via `pydantic-settings`
- **Never commit `.env` files** - they are gitignored

**AWS Lambda (Secrets Manager)**:
- The presence of `AWS_EXECUTION_ENV` environment variable triggers Secrets Manager loading
- Secrets are fetched from AWS Secrets Manager using the pattern: `gen-ai-on-aws/{stack_name}/{secret_name}`
- Default secret names:
  - `gen-ai-on-aws/{stack_name}/anthropic_api_key`
  - `gen-ai-on-aws/{stack_name}/langfuse_public_key`
  - `gen-ai-on-aws/{stack_name}/langfuse_secret_key`
- Custom secret names can be specified via environment variables:
  - `ANTHROPIC_API_KEY_SECRET_NAME`
  - `LANGFUSE_PUBLIC_KEY_SECRET_NAME`
  - `LANGFUSE_SECRET_KEY_SECRET_NAME`

**Implementation Details**:
- See `api/gen_ai_on_aws/config.py` for the secrets loading logic
- Secrets are loaded at module import time and set as environment variables
- Langfuse integration is automatically enabled if both public and secret keys are present


## Project Structure

VERY IMPORTANT: each directory has its own pyproject.toml file, with its own dependencies, its own tests, its own config.

- `/app`: FastAPI application code
- `/provisioning`: Pulumi infrastructure code


## Build & Deployment
- Run `app/build_lambda_package.sh` to create Lambda zip package
- **CRITICAL: NEVER run `pulumi up`, `pulumi destroy`, or any other Pulumi deployment commands.** Infrastructure deployment is ALWAYS done manually by the user.
- You may run `pulumi preview` to show what changes would be made, but only when explicitly asked.
- **A Claude Code hook is configured in `.claude/settings.json` to automatically block deployment commands** (`pulumi up`, `pulumi destroy`, `pulumi refresh`, `pulumi import`, stack mutations).

## Testing
- Framework: pytest with pytest-asyncio
- Run tests: `pytest` or `pytest app/gen_ai_on_aws/examples/test_examples.py`
- Single test: `pytest app/gen_ai_on_aws/examples/test_examples.py::test_hello`

## Code Quality Automation
- **Format**: Ruff (`ruff format`)
- **Linting**: Ruff (`ruff check`)
- **Type checking**: Pyright (`pyright`)
- **Automation**: Post-edit hooks automatically run these tools on every file edit (see `.claude/settings.json`)
- **Pre-commit hooks**: Configured for commit-time validation
- **Type annotations**: Used extensively throughout the codebase

## Conventions
- Descriptive function names (snake_case)
- Explicit error handling (usually returning None for failures)
- Type annotations for function parameters and return values
- Route organization: Uses FastAPI routers for structure
- Logging via standard Python logging module