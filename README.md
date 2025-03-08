# GenAI on AWS

This repo contains an example on how to quickly deploy a production ready GenAI app in AWS, using a serverless tech stack.


## General Architecture

## Structure

- `provisioning` directory contains the (Pulumi) scripts to create resources.
- `app` contains the python app code.
Each directory contains a different dependency set (pyproject file).
Dependencies at the root of the project aim to apply  consistent rules at repo level.


## Deployment

Install 

 - [uv](https://docs.astral.sh/uv/getting-started/installation/) python version manager & package manager
 - [Docker](https://docs.docker.com/engine/install/) to build zip files that contain app code


 Clone the repostory, then run commands below from the repo root.

 ### Build app 

 This will package code under `app/build/packages/package-<git-hash>.zip`

 ```fish
cd app
./build_lambda_package.sh
 ```


### Provision infrastructure and deploy code

 This uses Pulumi to create API and Lambda function taht runs the front API

 ```fish
cd provisioning
uv run pulumi login --local  ## stores state files on local disk under $HOME directory, but you can also store it on S3 / Pulumi Cloud
export PULUMI_CONFIG_PASSPHRASE=""  # encrypts secrets in state file, should not be empty
export AWS_DEFAULT_REGION=us-east-1  # choose where you want to deploy
export PULUMI_STACK=demo
uv run pulumi stack init $PULUMI_STACK  # creates a "demo" stack, you can create as many stacks as you want
```

Then, add your AWS credentials in environment variables (to simplify things, those credentials should be one attached to a role / user that has admin level credentials, or permissions to provision all resources needed)

```fish
export AWS_ACCESS_KEY_ID="ASIAxxx"
export AWS_SECRET_ACCESS_KEY="xxx"
export AWS_SESSION_TOKEN="xxx"
```

Store the Anthropic API key in AWS secrets manager so keys stay secure inside AWS, and code fetch them on demand at runtime (other LLMs / providers are supported through LiteLLM):

```fish
aws secretsmanager create-secret --secret-string '{"key": "sk-ant-xxx"}' --name "gen-ai-on-aws/$PULUMI_STACK/anthropic_api_key"
```

Create resources

```fish
uv run pulumi up -y
````

Call API

```fish
http POST $(pulumi stack output apigateway-rest-endpoint)"/extract-user" text="My name is Bob, I am 40 years old"
```

Look at the logs of Lambda function

```fish
aws logs tail --follow /aws/lambda/$(pulumi stack output lambda_function_name)
```


### [Optional] Setup LangFuse

Create a new project in Langfuse Cloud, and define those secrets to send tracing data to Langfuse

```fish
aws secretsmanager create-secret --secret-string '{"key": "pk-lf-xxx"}' --name "gen-ai-on-aws/$PULUMI_STACK/langfuse_public_key"
aws secretsmanager create-secret --secret-string '{"key": "sk-lf-xxx"}' --name "gen-ai-on-aws/$PULUMI_STACK/langfuse_secret_key"
```

## Development

```fish
cd app
uv sync
uv run fastapi
```

### Running Unit Tests

To run the unit tests:

```fish
cd app
uv run pytest
```

For more verbose output, use:

```fish
uv run pytest -v
```

To see test coverage:

```fish
uv run pytest --cov=gen_ai_on_aws; and uv run coverage html; and open htmlcov/index.html 
```

## TODO

- [ ] Add tag to all pulumi resources
- [ ] Architecture Diagram
- [ ] CI/CD with GH Actions
- [ ] Progressive deployments with CodeDeploy
- [x] integrate uv and direnv
- [x] packaging of Lambda
- [x] pre commit config
- [x] Lint, Type Checking (ruff), back
- [x] Use FastAPI for app
- [x] Make a first call to Bedrock / Anthropic
- [x] Setup unit tests
- [x] Add langfuse
- [ ] Add more info in langfuse tracing, such as xray trace id, app version
- [ ] Add SQS queue and worker
- [ ] Add aurora Postgres for RAG
- [ ] Monitoring
- [ ] Push response / result using a websocket
- [ ] What frontend to illustrate demo?
- [ ] Demo of LLM chain / patterns
