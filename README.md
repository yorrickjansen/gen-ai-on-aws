# GenAI on AWS

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
    subgraph "AWS Cloud"
        subgraph "API Gateway"
            api[API Gateway REST/HTTP API]
        end
        
        subgraph "AWS Lambda"
            lambda[Lambda Function<br>Python 3.13]
            worker[Worker Lambda<br>Async Processing]
        end
        
        subgraph "AWS Secrets Manager"
            secrets[Secrets Manager<br>API Keys]
        end
        
        subgraph "AWS SQS"
            sqs[SQS Queue<br>Async Requests]
        end
        
        subgraph "CloudWatch"
            logs[CloudWatch Logs]
            metrics[CloudWatch Metrics]
        end
        
    end
    
    subgraph "External Services"
        anthropic[Anthropic API<br>Claude Models]
        langfuse[LangFuse<br>Observability]
    end
    
    subgraph "Application Components"
        app[FastAPI Application]
        litellm[LiteLLM<br>Model Integration]
        mangum[Mangum<br>AWS Lambda Handler]
        routers[FastAPI Routers<br>Endpoints]
        processor[Worker Processor<br>Async LLM Processing]
    end
    
    client[Client] -->|HTTP Request| api
    api -->|Forward Request| lambda
    lambda -->|Log Events| logs
    lambda -->|Process Request| app
    app -->|Route Request| routers
    routers -->|Sync LLM Request| litellm
    routers -->|Async Request| sqs
    sqs -->|Trigger| worker
    worker -->|Process Message| processor
    processor -->|LLM Request| litellm
    litellm -->|LLM Call| anthropic
    lambda -->|Fetch API Keys| secrets
    worker -->|Fetch API Keys| secrets
    litellm -->|Trace LLM Calls| langfuse
    app -->|AWS Lambda Integration| mangum
    lambda -->|Publish Metrics| metrics
    worker -->|Publish Metrics| metrics
    worker -->|Log Events| logs
    
    classDef aws fill:#FF9900,stroke:#232F3E,color:white;
    classDef ext fill:#60A5FA,stroke:#2563EB,color:white;
    classDef app fill:#4ADE80,stroke:#16A34A,color:white;
    
    class api,lambda,worker,secrets,logs,metrics,sqs aws;
    class anthropic,langfuse ext;
    class app,litellm,mangum,routers,processor app;
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
http POST $(pulumi stack output apigateway-rest-endpoint)"/examples/extract-user" \
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
cd app
uv run uvicorn gen_ai_on_aws.main:app --reload
```

### Test the API Locally

```bash
http POST http://0.0.0.0:8000/examples/extract-user \
  text="My name is Bob, I am 40 years old, bb@gmail.com"
```

### Running Tests

```bash
cd app
uv run pytest                        # Run all tests
uv run pytest -v                     # Verbose output
uv run pytest --cov=gen_ai_on_aws    # Test coverage
```

Generate HTML coverage report:
```bash
uv run pytest --cov=gen_ai_on_aws && uv run coverage html && open htmlcov/index.html
```

## Roadmap

- ✅ FastAPI application with routers
- ✅ Lambda packaging 
- ✅ Anthropic/Bedrock integration
- ✅ LangFuse tracing
- ✅ Unit testing
- ✅ Architecture diagram
- ✅ SQS queue and worker processing
- ✅ CI/CD with GitHub Actions
- ⬜ Dynamic loading of prompt using Langfuse, for faster experimentation
- ⬜ LLM chain/pattern examples
- ⬜ Demo of n8n integration
- ⬜ RAG with Aurora PostgreSQL
- ⬜ Custom domain name, SSL certificate, IP whitelisting, usage plans to restrict access to API
- ⬜ Monitoring and alerts, with optional integration with Incidents Manager / Pager Duty
- ⬜ Lambda layers optimization for faster deployments
- ⬜ Progressive deployments for improved reliability in production (using CodeDeploy, triggered from GH Actions)
- ⬜ Frontend implementation for demo (optional websocket push)

## License

See the [LICENSE](LICENSE) file for details.
