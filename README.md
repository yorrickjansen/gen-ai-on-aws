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
pulumi login --local  ## stores state files on local disk under $HOME directory, but you can also store it on S3 / Pulumi Cloud

 ```

## Installation

This project uses `uv` to manage dependencies.
You also need Docker in order to package the code before deploying.

```fish
cd app
uv sync
```

Optionally, you can install Aider for AI coding

```fish
uv tool install --force --python python3.12 aider-chat@latest
uvx aider
```


## Package and deploy code

```fish
cd app
./build_lambda_package.sh
```

Then create resources in AWS

```fish
cd provisioning
pulumi up
```

Test endpoint

```fish
http GET (pulumi stack output apigateway-rest-endpoint)"/hello"
```

## Running Tests

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
uv run pytest --cov=gen_ai_on_aws
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
- [ ] Push response / result using a websocket
- [ ] What frontend to illustrate demo?
- [ ] Demo of LLM chain / patterns
