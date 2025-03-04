# GenAI on AWS

This repo contains an example on how to quickly deploy prod ready GenAI apps in AWS, using a serverless tech stack for minimum maintenance.


## General Architecture

## Structure

`provisioning` directory contains the scripts to create resources.
`app` contains the python app code.
Each directory contains a different dependency set (pyproject file).
Dependencies at the root of the project aim to apply  consistent rules at repo level.


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

- [x] integrate uv and direnv
- [x] packaging of Lambda
- [x] pre commit config
- [ ] CI/CD with GH Actions
- [x] Lint, Type Checking (ruff), back
- [x] Use FastAPI for app
- [ ] Make a first call to Bedrock
- [ ] Setup unit tests
- [ ] Choose an example of GenAI application
- [ ] Frontend?
- [ ] Progressive deployments with CodeDeploy
