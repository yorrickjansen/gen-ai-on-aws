# GenAI on AWS

[![CI/CD Pipeline](https://github.com/yorrickjansen/gen-ai-on-aws/actions/workflows/ci.yml/badge.svg)](https://github.com/yorrickjansen/gen-ai-on-aws/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yorrickjansen/gen-ai-on-aws/branch/main/graph/badge.svg)](https://codecov.io/gh/yorrickjansen/gen-ai-on-aws)

A production-ready GenAI application framework on AWS using a serverless architecture, for minimal maintenance & cost, and maximum scalability.

## Overview

This repository provides a complete solution for deploying GenAI applications on AWS with:

- FastAPI backend running on AWS Lambda
- API Gateway for HTTP endpoints
- Anthropic/Claude integration (with support for other LLMs via LiteLLM)
- Infrastructure as Code using Pulumi
- LangFuse for observability and tracing
- Comprehensive testing and development tools

## Architecture Diagram

```mermaid
graph TB
    %% Main components
    client[Client]
    api[API Gateway]
    lambda[API Lambda<br>FastAPI]
    worker[Worker Lambda]
    sqs[SQS Queue]
    secrets[Secrets Manager]
    llm[LLM APIs<br>Claude/Bedrock]
    observe[LangFuse<br>Observability]
    cicd[GitHub Actions<br>CI/CD]
    
    %% Flow
    client -->|HTTP Request| api
    api -->|Forward| lambda
    lambda -->|Sync Request| llm
    lambda -->|Async Request| sqs
    sqs -->|Trigger| worker
    worker -->|Process| llm
    
    %% Auxiliary connections
    lambda -.->|Fetch Keys| secrets
    worker -.->|Fetch Keys| secrets
    lambda -.->|Traces| observe
    worker -.->|Traces| observe
    cicd -.->|Deploy| lambda
    cicd -.->|Deploy| worker
    
    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,color:white;
    classDef ext fill:#60A5FA,stroke:#2563EB,color:white;
    classDef cicd fill:#F472B6,stroke:#DB2777,color:white;
    
    class api,lambda,worker,sqs,secrets aws;
    class llm,observe ext;
    class cicd cicd;
```

## Repository Structure

- `api/` - FastAPI application code
  - `gen_ai_on_aws/` - Main application
  - `build/` - Build artifacts
- `worker/` - Lambda worker code for async processing
  - `worker/` - Main worker logic
  - `build/` - Build artifacts
- `provisioning/` - Pulumi IaC for AWS resources
- `specs/` - AI Coding prompt
- `ai-docs/` - Reference documentation for AI coding, scraped with Firecrawl MCP (Model Context Protocol)
- `.github/workflows/` - CI/CD pipeline configurations

Each directory has its own dependency set (pyproject.toml). Root dependencies enforce consistent standards across the repository.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Python version and package manager
- [Docker](https://docs.docker.com/engine/install/) - Required for building Lambda packages
- [httpie](https://httpie.io/cli) - Modern HTTP client (optional but recommended)
- AWS Account with appropriate permissions
- Anthropic API key (if using Claude)

## Deployment

TLDR

```bash
./build_lambda_packages.sh; and ./run_pulumi.sh up -y
```

### 1. Build the Lambda Packages

The project provides flexible options for building Lambda deployment packages:

```bash
# Option 1: Build both API and worker packages from repository root
./build_lambda_packages.sh

# Option 2: Build only the API package
./api/build_lambda_package.sh

# Option 3: Build only the worker package (with optional version)
./worker/build_lambda_package.sh [version]
```

These scripts can be run from either the repository root or their respective directories. The API package uses the git commit hash for versioning, while the worker package uses either the provided version parameter or a timestamp.

This creates deployment packages at:
- API: `api/build/packages/api-package-<git-hash>.zip`
- Worker: `worker/build/packages/worker-package-<version>.zip`

### 2. Provision AWS Infrastructure

```bash
cd provisioning
uv run pulumi login --local  # Store state locally (can also use S3/Pulumi Cloud)
export PULUMI_CONFIG_PASSPHRASE="your-passphrase"  # For state file encryption
export AWS_DEFAULT_REGION=us-east-1
export PULUMI_STACK=dev
uv run pulumi stack init $PULUMI_STACK
```

### 3. Configure AWS Credentials

```bash
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export AWS_SESSION_TOKEN="YOUR_SESSION_TOKEN"  # If using temporary credentials
```

### 4. Store API Keys Securely

```bash
aws secretsmanager create-secret \
  --secret-string '{"key": "sk-ant-your-key"}' \
  --name "gen-ai-on-aws/$PULUMI_STACK/anthropic_api_key"
```

### 5. Deploy Resources

```bash
uv run pulumi up -y
```

### 6. Test the Deployment

```bash
http POST $(pulumi stack output apigatewayv2-http-endpoint)"/examples/extract-user" \
  text="My name is Bob, I am 40 years old"
```

### 7. Monitor Lambda Logs

```bash
aws logs tail --follow /aws/lambda/$(pulumi stack output lambda_function_name)
```

## Advanced Configuration

### LangFuse Integration

```bash
aws secretsmanager create-secret \
  --secret-string '{"key": "pk-lf-xxx"}' \
  --name "gen-ai-on-aws/$PULUMI_STACK/langfuse_public_key"

aws secretsmanager create-secret \
  --secret-string '{"key": "sk-lf-xxx"}' \
  --name "gen-ai-on-aws/$PULUMI_STACK/langfuse_secret_key"
```

## Cost Considerations

The serverless architecture of this solution minimizes costs while maintaining scalability:

| AWS Service | Cost Factors | Optimization |
|-------------|--------------|--------------|
| Lambda | $0.0000166667/GB-s, $0.20/1M requests | 128MB-256MB memory, cold start <100ms |
| API Gateway | $1.00/1M requests | HTTP API is cheaper than REST API |
| SQS | $0.40/1M requests | Standard queue for most use cases |
| Secrets Manager | $0.40/secret/month, $0.05/10K API calls | Reuse secrets across environments |
| CloudWatch | $0.30/GB ingest, $0.03/1M metrics | Filter logs, adjust retention |

**Estimated Monthly Cost (low-volume):**
* 100K requests: ~$1-3/month + LLM API costs
* No always-on resources means no idle costs

## Local Development

### Run the FastAPI Server

```bash
cd api
uv run uvicorn gen_ai_on_aws.main:app --reload
```

### Test the API Locally

```bash
http POST http://0.0.0.0:8000/examples/extract-user \
  text="My name is Bob, I am 40 years old, bb@gmail.com"
```

### Running Tests

```bash
cd api
uv run pytest                        # Run all tests
uv run pytest -v                     # Verbose output
uv run pytest --cov=gen_ai_on_aws    # Test coverage
```

Generate HTML coverage report:
```bash
uv run pytest --cov=gen_ai_on_aws && uv run coverage html && open htmlcov/index.html
```

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment with environment-specific configurations:

### Pipeline Overview

1. **Triggers:**
   - Automatically runs on push to main branch
   - Automatically runs on pull requests to main branch
   - Manual trigger via workflow dispatch with environment selection (dev/demo)

2. **CI Workflow:**
   - **Lint:** Code quality checks with ruff, isort, and other tools
   - **Test API:** API unit tests with pytest and codecov integration
   - **Test Worker:** Worker unit tests with pytest and code coverage
   - **Test API Start:** Verifies API can start and serve requests
   - **Test Pulumi:** Tests infrastructure code with Pulumi
   - **Build:** Creates Lambda deployment packages for API and worker

3. **CD Workflow:**
   - Runs automatically when code is pushed to `main` (dev environment) or `releases/demo` (demo environment)
   - Uses AWS OIDC authentication for secure access to AWS resources
   - Downloads Lambda packages built by the CI workflow
   - Deploys the infrastructure using Pulumi

4. **AWS Authentication:**
   - Uses OIDC (OpenID Connect) for secure authentication to AWS
   - Environment-specific AWS account IDs for multi-account deployments
   - IAM role "github-actions" with controlled permissions

5. **Environment Configuration:**
   - Environment-specific secrets for AWS credentials and API keys
   - GitHub Environments for "dev" and "demo" with appropriate protection rules
   - Pulumi stacks named after environments for infrastructure management

### CI/CD Setup Instructions

1. **Configure AWS OIDC Integration:**
   ```bash
   # Set the GitHub repository in Pulumi config
   cd provisioning
   pulumi config set github_repo "your-org/your-repo"
   pulumi up
   ```

2. **Configure GitHub Secrets:**
   - `AWS_ROLE_TO_ASSUME`: The ARN of the role created by Pulumi
   - `AWS_REGION`: The AWS region to deploy to (e.g., `us-east-1`)
   - `PULUMI_PASSPHRASE`: A passphrase for encrypting the Pulumi state
   - `CODECOV_TOKEN`: Token for uploading coverage reports (optional)

3. **Branch Protection Rules:**
   - Require status checks to pass before merging
   - Require review before merging
   - Do not allow bypassing the above settings

See the [CI/CD workflow files](.github/workflows/) for detailed configuration.

## Roadmap

- ✅ FastAPI application with routers
- ✅ Lambda packaging 
- ✅ Anthropic/Bedrock integration
- ✅ LangFuse tracing
- ✅ Unit testing
- ✅ Architecture diagram
- ✅ SQS queue and worker processing
- ✅ CI/CD with GitHub Actions
- ✅ Codecov integration
- ⬜ LLM chain/pattern examples
- ⬜ Demo of n8n integration
- ⬜ Dynamic loading of prompt using Langfuse, for faster experimentation
- ⬜ RAG with Aurora PostgreSQL
- ⬜ PII data handling (log retention, masking, etc.)
- ⬜ Cost tracking and alerts
- ⬜ Demo of Bedrock, Kendra, Lex, etc... integration
- ⬜ Custom domain name, SSL certificate, IP whitelisting, usage plans to restrict access to API
- ⬜ Monitoring, alerts, tracing, backups, with optional integration with Incidents Manager / Pager Duty
- ⬜ Lambda layers optimization for faster deployments
- ⬜ Progressive deployments for improved reliability in production (using CodeDeploy, triggered from GH Actions)
- ⬜ Frontend implementation for demo (optional websocket push)
- ⬜ Scaling configuration for Lambda functions (concurrency, memory, timeout)

## License

See the [LICENSE](LICENSE) file for details.

