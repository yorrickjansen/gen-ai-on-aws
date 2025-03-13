# Async Processing for LLM calls

## Overview

We want to demonstrate async processing of LLM calls using AWS SQS and AWS Lambda.

## Architecture

We need to implement an FastAPI endpoint that will be used to send messages to the queue.

The queue will be used to process the LLM calls asynchronously.

A new Lambda function will be used to process the messages from the queue.


## Implementation details

### app / api

`app` directory contains the FastAPI application, that is already packaged for AWS Lambda.

We need to add a new endpoint `def extract_user_async(request: ExtractUserRequest)` to the application that will be used to send messages to the queue.

This endpoint will be used to send messages to the queue.

`app/tests/` need to be updated to include the new endpoint.

Use "pydantic-settings" to manage the config (need update).

### worker
We then want a new directory `worker` that will contain the code for the Lambda function that will be used to process the messages from the queue.
This directory will be packaged into another lambda function, using the same packaging as the `app` directory; it will also have its own dependencies, using uv.

The worker will receive messages from the queue, and will process them the same way as the `extract_user` endpoint (using instrutor, litellm, langfuse, etc). config.py will need to copied into the `worker` directory, and used.

Use "pydantic-settings" to manage the config.

`worker/tests/` need to be updated to test worker features (for now, it's just implementing user extraction, but we can add more tests later).


### provisioning

The `provisioning` directory contains the code for the provisioning of the infrastructure.

We need to provision the following resources:

- SQS queue
- Worker Lambda function
- IAM role and policy for the worker Lambda function



## Project structure

.
├── pyproject.toml             # project deps, such as linting, formatting tools
├── provisioning/
│   ├── pyproject.toml         # Provisioning-specific dependencies
├── app/
│   ├── pyproject.toml         # App/api specific dependencies
│   ├── gen_ai_on_aws/    # Your app package name
│   │   ├── __init__.py
│   │   ├── examples/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── request.py
│   │   │   └── queue.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── queue_service.py
│   │   ├── config.py (use pydantic-settings, loads sensitive data from AWS Secrets Manager)
│   │   └── main.py (entrypoint for the FastAPI application)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models/
│       │   └── test_request.py
│       └── test_services/
│           └── test_queue_service.py
├── worker/
│   ├── pyproject.toml        # Worker-specific dependencies
│   ├── src/
│   │   └── worker/
│   │       ├── __init__.py
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   └── queue.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   └── processor.py
│   │       ├── config.py (use pydantic-settings, loads sensitive data from AWS Secrets Manager)
│   │       └── main.py (entrypoint for the worker Lambda function)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_processor.py
└── README.md



## Validation

- run uv run pytest --cov=app
- run uv run pytest --cov=worker
- in provisioning, run `pulumi preview`






