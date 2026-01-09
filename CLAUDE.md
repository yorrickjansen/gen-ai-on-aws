# CLAUDE.md - Gen-AI-on-AWS Codebase Guidelines

## Core Principles
- **Never assume missing context.** Ask clarifying questions if the request is ambiguous or incomplete.
- **Never hallucinate libraries or functions.** Only use known, verified Python packages. If unsure, use Perplexity to verify (never use WebSearch).
- **Always use Perplexity for web research.** When you need to look up information, use the Perplexity MCP tool (`mcp__perplexity-ask__perplexity_ask`), not WebSearch.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to do so.

## Code Structure & Modularity
- **Keep files concise.** Never create a file longer than 500 lines of code. If a file approaches this limit, refactor it by splitting it into smaller, focused modules.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports.** Prefer relative imports for modules within the same package.
- **Each module should define its own models, services, and an optional data layer file if it makes sense.**

## Style & Conventions
- **Use Python** as the primary language.
- **Follow PEP8 standards.** Use type hints for all function signatures and variables where appropriate.
- **Format code with `ruff` and lint with `pyright`.** Always run `ruff format .` and `pyright .` after generating or modifying code to ensure compliance.
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
- **Always create Pytest unit tests for new features** (e.g., functions, classes, API routes).
- **Update existing unit tests** whenever the logic they cover is modified.
- **Organize tests in a top-level `/tests` directory** that mirrors the main application's structure.
- **Ensure comprehensive test coverage** for each feature, including at a minimum:
  - One test for the expected, "happy path" use case.
  - One test for a known edge case.
  - One test for an expected failure or error case.
- **Always run the full test suite from the project root** after implementing any change to verify that nothing has broken (e.g., `uv run pytest`).
- **When implementing cli commands, test them with 'virtual-receptionist n8n --help' and 'virtual-receptionist n8n get-executions --help' for instance, to test n8n**
- **Then, run other tests for read-only commands**

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

### Logging
- **Always use `loguru` for logging.**
- **Configure logging to output in a structured (JSON) format.**
- **Add relevant context to the logger** whenever possible (e.g., request ID, user ID) to simplify debugging and tracing.

### HTTP Calls
- **Always use `httpie`** for making HTTP calls from the terminal (e.g., `http GET ...`).


## Project Structure

VERY IMPORTANT: each directory has its own pyproject.toml file, with its own dependencies, its own tests, its own config.

- `/app`: FastAPI application code
- `/provisioning`: Pulumi infrastructure code


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