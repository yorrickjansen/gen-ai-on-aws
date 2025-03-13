# CI/CD Setup for Gen-AI-on-AWS

This project uses GitHub Actions for continuous integration and deployment.

## CI Workflow

The CI workflow (`ci.yml`) runs on every push to the main branch and pull requests. It performs the following steps:

1. **Linting**: Runs ruff, isort, and other code quality checks
2. **API Tests**: Runs unit tests for the API component with code coverage
3. **Worker Tests**: Runs unit tests for the worker component with code coverage
4. **API Startup Test**: Verifies the API can start correctly
5. **Pulumi Test**: Validates Pulumi infrastructure configuration
6. **Build**: Creates Lambda deployment packages for both API and worker components

## CD Workflow

The CD workflow (`cd.yml`) deploys the application to AWS. It:

1. Runs automatically when code is pushed to `main` (dev environment) or `releases/demo` (demo/prod environment)
2. Uses AWS OIDC authentication for secure access to AWS resources
3. Downloads Lambda packages built by the CI workflow
4. Deploys the infrastructure using Pulumi

## Setup Instructions

### 1. Configure AWS OIDC Integration

To enable GitHub Actions to authenticate with AWS:

```bash
# Set the GitHub repository in Pulumi config
cd provisioning
pulumi config set github_repo "your-org/your-repo"
pulumi up
```

This creates the necessary OIDC provider and IAM roles in AWS. The role ARN will be output, which you need for the next step.

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

- `AWS_ROLE_TO_ASSUME`: The ARN of the role created by Pulumi (from previous step)
- `AWS_REGION`: The AWS region to deploy to (e.g., `us-east-1`)
- `PULUMI_PASSPHRASE`: A passphrase for encrypting the Pulumi state
- `CODECOV_TOKEN`: Token for uploading coverage reports (optional)

### 3. Initialize Pulumi Stacks

Create and configure Pulumi stacks for each environment:

```bash
cd provisioning
pulumi stack init dev
pulumi config set app_version latest
pulumi config set model_name claude-3-haiku-20240307
# Set other required configurations

# Repeat for demo
pulumi stack init demo
# Same configurations as above
```

### 4. Add Status Badges

Add the CI status badge to your main README.md:

```markdown
![CI](https://github.com/your-org/your-repo/actions/workflows/ci.yml/badge.svg)
```

For code coverage badge, set up Codecov integration first, then add:

```markdown  
[![codecov](https://codecov.io/gh/your-org/your-repo/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/your-repo)
```

### 5. Branch Protection Rules

Set up branch protection rules in GitHub:
- Require status checks to pass before merging
- Require review before merging
- Do not allow bypassing the above settings

## Troubleshooting

- **CI Failures**: Check the specific job logs to identify and fix the issue
- **CD Failures**: Verify AWS credentials and Pulumi configuration
- **Missing Artifacts**: Ensure CI workflow completes successfully before CD runs