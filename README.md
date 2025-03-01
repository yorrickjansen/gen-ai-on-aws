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


## Package and deploy code

```
cd app
./build_lambda_package.sh
```

Then


## TODO
 - integrate uv and direnv
 - packaging of Lambda
 - pre commit config
 - CI/CD with GH Actions
 - Lint, Type Checking (ruff), back
 - Setup unit tests
 - Use FastAPI for app
 - Choose an example of GenAI application
 - Frontend?
 - Progressive deployments