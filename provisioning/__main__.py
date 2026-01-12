import glob
import json
import os

import iam
import layers
import logs
import monitoring
import pulumi
import pulumi_aws as aws
from github_actions import create_github_actions_oidc_provider

region = os.environ.get("AWS_DEFAULT_REGION")
config = pulumi.Config()
custom_stage_name = "stage"

stack_name = pulumi.get_stack()

# Get logging level from config
logging_level = logs.get_logging_level()

##################
## CloudWatch Log Groups
##################

# Create log groups first (they must exist before the Lambda functions)
api_function_name = f"{stack_name}_gen-ai-on-aws"
worker_function_name = f"{stack_name}_gen-ai-on-aws-worker"

# Create the log groups
log_groups = logs.create_log_groups(
    stack_name=stack_name,
    api_function_name=api_function_name,
    worker_function_name=worker_function_name,
)

##################
## Lambda Function
##################

# Create a Lambda function, using code from the `./api` folder.

# pulumi up -c APP_VERSION=latest
app_version = config.require("app_version")
model_name = config.require("model_name")

if app_version == "latest":
    # find the latest file named `api-*.zip` in the `api/build/packages` folder, using file timestamp
    list_of_files = glob.glob("../api/build/packages/api-*.zip")
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Using latest app version: {latest_file}")
    code = pulumi.FileArchive(latest_file)
else:
    print(f"Using app version: {app_version}")
    code = pulumi.FileArchive(f"../api/build/packages/api-{app_version}.zip")

######################
## SQS Queue and DLQ
######################

# Create a Dead Letter Queue for failed messages
dlq = aws.sqs.Queue(
    "dead-letter-queue",
    name=f"{stack_name}-dead-letter-queue",
    message_retention_seconds=1209600,  # 14 days
    receive_wait_time_seconds=20,  # Long polling
    tags={
        "Name": f"{stack_name}-dead-letter-queue",
        "Environment": stack_name,
    },
)

# Create a standard SQS queue for async processing with DLQ configuration
sqs_queue = aws.sqs.Queue(
    "async-processing-queue",
    name=f"{stack_name}-async-processing-queue",
    visibility_timeout_seconds=300,  # 5 minutes, same as Lambda timeout
    message_retention_seconds=86400,  # 1 day
    receive_wait_time_seconds=20,  # Long polling
    redrive_policy=dlq.arn.apply(
        lambda arn: json.dumps(
            {
                "deadLetterTargetArn": arn,
                "maxReceiveCount": 3,  # After 3 failed processing attempts, send to DLQ
            }
        )
    ),
    tags={
        "Name": f"{stack_name}-async-processing-queue",
        "Environment": stack_name,
    },
)

# Create a redrive allow policy for the DLQ
dlq_redrive_allow_policy = aws.sqs.RedriveAllowPolicy(
    "dlq-redrive-allow-policy",
    queue_url=dlq.id,
    redrive_allow_policy=sqs_queue.arn.apply(
        lambda arn: json.dumps(
            {"redrivePermission": "byQueue", "sourceQueueArns": [arn]}
        )
    ),
)

# Create a policy document for the queue
queue_policy_document = sqs_queue.arn.apply(
    lambda arn: {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                ],
                "Resource": arn,
            }
        ],
    }
)

# Create the queue policy
queue_policy = aws.sqs.QueuePolicy(
    "queue-policy",
    queue_url=sqs_queue.id,
    policy=queue_policy_document.apply(lambda doc: json.dumps(doc)),
)

##################
## S3 Bucket for Lambda Layers
##################

# Use existing DevOps bucket for storing large Lambda layers (>50MB)
layer_storage_bucket_name = "175314215331-devops-eu-central-1"

##################
## Lambda Layers
##################

# Get or create API Lambda layer (hash-based, cached in AWS)
api_layer_arn = layers.get_layer_for_lambda(
    name="api",
    lock_file_path="../api/uv.lock",
    s3_bucket=layer_storage_bucket_name,  # Use string, not Output
    build_dir="build/layers",
)

pulumi.export("api_layer_arn", api_layer_arn)

##################
## API Lambda
##################

lambda_func = aws.lambda_.Function(
    "app",
    name=api_function_name,  # Use the same name we used for log group
    role=iam.lambda_role.arn,
    runtime="python3.13",
    handler="gen_ai_on_aws.main.handler",
    timeout=30,
    memory_size=256,
    code=code,
    layers=[api_layer_arn],  # Add the dependencies layer
    # source_code_hash=TODO,
    environment={
        "variables": {
            "APP_VERSION": app_version,
            "MODEL": model_name,
            "STACK_NAME": stack_name,
            "LOGGING_LEVEL": logging_level,
            "ANTHROPIC_API_KEY_SECRET_NAME": f"gen-ai-on-aws/{stack_name}/"
            + config.require("anthropic_api_key_secret_name"),
            "LANGFUSE_PUBLIC_KEY_SECRET_NAME": f"gen-ai-on-aws/{stack_name}/"
            + config.require("langfuse_public_key_secret_name"),
            "LANGFUSE_SECRET_KEY_SECRET_NAME": f"gen-ai-on-aws/{stack_name}/"
            + config.require("langfuse_secret_key_secret_name"),
            "LANGFUSE_HOST": config.require("langfuse_host"),
            "SQS_QUEUE_URL": sqs_queue.url,
        },
    },
    # Add explicit dependency on log group
    opts=pulumi.ResourceOptions(depends_on=[log_groups["api_lambda_log_group"]]),
)

##################
## Worker Lambda
##################

# Load the worker code
worker_version = config.get("worker_version", "latest")

if worker_version == "latest":
    list_of_files = glob.glob("../worker/build/packages/worker-*.zip")
    if list_of_files:
        latest_worker_file = max(list_of_files, key=os.path.getctime)
        print(f"Using latest worker version: {latest_worker_file}")
        worker_code = pulumi.FileArchive(latest_worker_file)
    else:
        print("No worker package found. Please build the worker package first.")
        worker_code = None
else:
    print(f"Using worker version: {worker_version}")
    worker_code = pulumi.FileArchive(
        f"../worker/build/packages/worker-{worker_version}.zip"
    )

# Initialize worker_lambda to None (will be set if worker_code exists)
worker_lambda: aws.lambda_.Function | None = None

if worker_code:
    # Get or create Worker Lambda layer (hash-based, cached in AWS)
    worker_layer_arn = layers.get_layer_for_lambda(
        name="worker",
        lock_file_path="../worker/uv.lock",
        s3_bucket=layer_storage_bucket_name,  # Use string, not Output
        build_dir="build/layers",
    )

    pulumi.export("worker_layer_arn", worker_layer_arn)

    # Create the worker Lambda function
    worker_lambda = aws.lambda_.Function(
        "worker",
        name=worker_function_name,  # Use the same name we used for log group
        role=iam.worker_lambda_role.arn,
        runtime="python3.13",
        handler="worker.main.lambda_handler",
        timeout=300,  # 5 minutes
        memory_size=512,
        code=worker_code,
        layers=[worker_layer_arn],  # Add the dependencies layer
        environment={
            "variables": {
                "WORKER_VERSION": worker_version
                if worker_version != "latest"
                else "latest",
                "MODEL": model_name,
                "STACK_NAME": stack_name,
                "LOGGING_LEVEL": logging_level,
                "ANTHROPIC_API_KEY_SECRET_NAME": f"gen-ai-on-aws/{stack_name}/"
                + config.require("anthropic_api_key_secret_name"),
                "LANGFUSE_PUBLIC_KEY_SECRET_NAME": f"gen-ai-on-aws/{stack_name}/"
                + config.require("langfuse_public_key_secret_name"),
                "LANGFUSE_SECRET_KEY_SECRET_NAME": f"gen-ai-on-aws/{stack_name}/"
                + config.require("langfuse_secret_key_secret_name"),
                "LANGFUSE_HOST": config.require("langfuse_host"),
            },
        },
        # Add explicit dependency on log group
        opts=pulumi.ResourceOptions(depends_on=[log_groups["worker_lambda_log_group"]]),
    )

    # Create event source mapping from SQS to Lambda
    event_source_mapping = aws.lambda_.EventSourceMapping(
        "worker-event-source-mapping",
        event_source_arn=sqs_queue.arn,
        function_name=worker_lambda.name,
        batch_size=1,
        maximum_batching_window_in_seconds=0,
    )


#########################################################################
##
## HTTP API (API Gateway V2)
##    /{proxy+} - passes all requests through to the lambda function
##
#########################################################################

http_endpoint = aws.apigatewayv2.Api(
    "api-endpoint", name=f"{stack_name}_gen-ai-on-aws", protocol_type="HTTP"
)

http_lambda_backend = aws.apigatewayv2.Integration(
    "lambda_integration",
    api_id=http_endpoint.id,
    integration_type="AWS_PROXY",
    connection_type="INTERNET",
    integration_method="POST",
    integration_uri=lambda_func.arn,
    passthrough_behavior="WHEN_NO_MATCH",
)

url = http_lambda_backend.integration_uri

http_route = aws.apigatewayv2.Route(
    "proxy-route",
    api_id=http_endpoint.id,
    route_key="ANY /{proxy+}",
    target=http_lambda_backend.id.apply(lambda targetUrl: "integrations/" + targetUrl),
)

http_stage = aws.apigatewayv2.Stage(
    "stage",
    name=custom_stage_name,
    api_id=http_endpoint.id,
    route_settings=[
        {
            "route_key": http_route.route_key,
            "throttling_burst_limit": 1,
            "throttling_rate_limit": 0.5,
        }
    ],
    access_log_settings={
        "destination_arn": log_groups["api_gateway_log_group"].arn,
        "format": '{"requestId":"$context.requestId", "ip":"$context.identity.sourceIp", "requestTime":"$context.requestTime", "httpMethod":"$context.httpMethod", "routeKey":"$context.routeKey", "status":"$context.status", "protocol":"$context.protocol", "responseLength":"$context.responseLength", "path":"$context.path", "integrationStatus":"$context.integrationStatus", "integrationLatency":"$context.integrationLatency", "responseLatency":"$context.responseLatency"}',
    },
    auto_deploy=True,
    # Add explicit dependency on the API Gateway log group
    opts=pulumi.ResourceOptions(depends_on=[log_groups["api_gateway_log_group"]]),
)

# Give permissions from API Gateway to invoke the Lambda
http_invoke_permission = aws.lambda_.Permission(
    "api-http-lambda-permission",
    action="lambda:invokeFunction",
    function=lambda_func.name,
    principal="apigateway.amazonaws.com",
    source_arn=http_endpoint.execution_arn.apply(lambda arn: arn + "*/*"),
)

# Export the https endpoint of the HTTP API
# For API Gateway HTTP APIs, we can adjust the Lambda integration to handle stage name in path
pulumi.export(
    "apigatewayv2-http-endpoint",
    http_endpoint.api_endpoint.apply(
        lambda endpoint: f"{endpoint}/{custom_stage_name}/"
    ),
)
pulumi.export("lambda_function_name", lambda_func.name)
pulumi.export("sqs_queue_url", sqs_queue.url)
pulumi.export("dlq_url", dlq.url)
if worker_lambda:
    pulumi.export("worker_lambda_function_name", worker_lambda.name)

##########################
## Monitoring and Alarms
##########################

# Get the monitoring email from Pulumi config (if set)
monitoring_email = config.get("monitoring_email")

# Get the worker lambda to pass to monitoring (could be None)
worker_lambda_instance = worker_lambda

# Create monitoring resources (CloudWatch alarms, dashboard, and optional SNS topic)
monitoring_resources, dashboard_url = monitoring.create_monitoring_resources(
    stack_name=stack_name,
    region=region,
    lambda_func=lambda_func,
    worker_lambda=worker_lambda_instance,
    sqs_queue=sqs_queue,
    dlq=dlq,
    http_endpoint=http_endpoint,
    http_stage=http_stage,
    monitoring_email=monitoring_email,
)

# Export the dashboard URL and log retention information
pulumi.export("dashboard_url", dashboard_url)
pulumi.export("logs_retention_days", 30)

# Create GitHub Actions OIDC provider for CI/CD
github_repo = config.get("github_repo")
if github_repo:
    create_github_actions_oidc_provider(github_repo)
