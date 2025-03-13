# AWS Lambda Function

Provides a Lambda Function resource. Lambda allows you to trigger execution of code in response to events in AWS, enabling serverless backend solutions. The Lambda Function itself includes source code and runtime configuration.

For information about Lambda and how to use it, see [What is AWS Lambda?](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)

## Example Usage

### Basic Example

```python
import pulumi
import pulumi_archive as archive
import pulumi_aws as aws

assume_role = aws.iam.get_policy_document(statements=[{
    "effect": "Allow",
    "principals": [{
        "type": "Service",
        "identifiers": ["lambda.amazonaws.com"],
    }],
    "actions": ["sts:AssumeRole"],
}])
iam_for_lambda = aws.iam.Role("iam_for_lambda",
    name="iam_for_lambda",
    assume_role_policy=assume_role.json)
lambda_ = archive.get_file(type="zip",
    source_file="lambda.js",
    output_path="lambda_function_payload.zip")
test_lambda = aws.lambda_.Function("test_lambda",
    code=pulumi.FileArchive("lambda_function_payload.zip"),
    name="lambda_function_name",
    role=iam_for_lambda.arn,
    handler="index.test",
    source_code_hash=lambda_.output_base64sha256,
    runtime=aws.lambda_.Runtime.NODE_JS18D_X,
    environment={
        "variables": {
            "foo": "bar",
        },
    })
```

### Lambda Layers

```python
import pulumi
import pulumi_aws as aws

example = aws.lambda_.LayerVersion("example")
example_function = aws.lambda_.Function("example", layers=[example.arn])
```

### Lambda Ephemeral Storage

Lambda Function Ephemeral Storage (`/tmp`) allows you to configure the storage up to `10` GB. The default value is set to `512` MB.

```python
import pulumi
import pulumi_aws as aws

assume_role = aws.iam.get_policy_document(statements=[{
    "effect": "Allow",
    "principals": [{
        "type": "Service",
        "identifiers": ["lambda.amazonaws.com"],
    }],
    "actions": ["sts:AssumeRole"],
}])
iam_for_lambda = aws.iam.Role("iam_for_lambda",
    name="iam_for_lambda",
    assume_role_policy=assume_role.json)
test_lambda = aws.lambda_.Function("test_lambda",
    code=pulumi.FileArchive("lambda_function_payload.zip"),
    name="lambda_function_name",
    role=iam_for_lambda.arn,
    handler="index.test",
    runtime=aws.lambda_.Runtime.NODE_JS18D_X,
    ephemeral_storage={
        "size": 10240,
    })
```

### CloudWatch Logging and Permissions

For more information about CloudWatch Logs for Lambda, see the [Lambda User Guide](https://docs.aws.amazon.com/lambda/latest/dg/monitoring-functions-logs.html).

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
lambda_function_name = config.get("lambdaFunctionName")
if lambda_function_name is None:
    lambda_function_name = "lambda_function_name"
# This is to optionally manage the CloudWatch Log Group for the Lambda Function.
# If skipping this resource configuration, also add "logs:CreateLogGroup" to the IAM policy below.
example = aws.cloudwatch.LogGroup("example",
    name=f"/aws/lambda/{lambda_function_name}",
    retention_in_days=14)
# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
lambda_logging = aws.iam.get_policy_document(statements=[{
    "effect": "Allow",
    "actions": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
    ],
    "resources": ["arn:aws:logs:*:*:*"],
}])
lambda_logging_policy = aws.iam.Policy("lambda_logging",
    name="lambda_logging",
    path="/",
    description="IAM policy for logging from a lambda",
    policy=lambda_logging.json)
lambda_logs = aws.iam.RolePolicyAttachment("lambda_logs",
    role=iam_for_lambda["name"],
    policy_arn=lambda_logging_policy.arn)
test_lambda = aws.lambda_.Function("test_lambda",
    name=lambda_function_name,
    logging_config={
        "log_format": "Text",
    },
    opts = pulumi.ResourceOptions(depends_on=[
            lambda_logs,
            example,
        ]))
```

## Function Resource Properties

The Function resource accepts the following properties:

### Required Inputs

- `role` (str) - Amazon Resource Name (ARN) of the function's execution role. The role provides the function's identity and access to AWS services and resources.

### Optional Inputs

- `architectures` (List[str]) - Instruction set architecture for your Lambda function. Valid values are `["x86_64"]` and `["arm64"]`. Default is `["x86_64"]`.
- `code` (pulumi.Archive) - Path to the function's deployment package within the local filesystem. Exactly one of `filename`, `image_uri`, or `s3_bucket` must be specified.
- `code_signing_config_arn` (str) - To enable code signing for this function, specify the ARN of a code-signing configuration.
- `dead_letter_config` (dict) - Configuration block for dead letter queue configuration.
- `description` (str) - Description of what your Lambda Function does.
- `environment` (dict) - Configuration block for environment variables.
- `ephemeral_storage` (dict) - The amount of Ephemeral storage (`/tmp`) to allocate for the Lambda Function in MB. Default is `512` MB.
- `file_system_config` (dict) - Configuration block for Amazon EFS file system.
- `handler` (str) - Function entrypoint in your code.
- `image_config` (dict) - Configuration block for container image settings.
- `image_uri` (str) - ECR image URI containing the function's deployment package.
- `kms_key_arn` (str) - Amazon Resource Name (ARN) of the AWS KMS key used to encrypt environment variables.
- `layers` (List[str]) - List of Lambda Layer Version ARNs (maximum of 5) to attach to your Lambda Function.
- `logging_config` (dict) - Configuration block used to specify advanced logging settings.
- `memory_size` (int) - Amount of memory in MB your Lambda Function can use at runtime. Defaults to `128`.
- `name` (str) - Unique name for your Lambda Function.
- `package_type` (str) - Lambda deployment package type. Valid values are `Zip` and `Image`. Defaults to `Zip`.
- `publish` (bool) - Whether to publish creation/change as new Lambda Function Version. Defaults to `false`.
- `reserved_concurrent_executions` (int) - Amount of reserved concurrent executions for this lambda function.
- `runtime` (str | aws.lambda_.Runtime) - Identifier of the function's runtime.
- `s3_bucket` (str) - S3 bucket location containing the function's deployment package.
- `s3_key` (str) - S3 key of an object containing the function's deployment package.
- `s3_object_version` (str) - Object version containing the function's deployment package.
- `snap_start` (dict) - Snap start settings block.
- `source_code_hash` (str) - Used to trigger replacement when source code changes.
- `tags` (Mapping[str, str]) - Map of tags to assign to the object.
- `timeout` (int) - Amount of time your Lambda Function has to run in seconds. Defaults to `3`.
- `tracing_config` (dict) - Configuration block for X-Ray tracing.
- `vpc_config` (dict) - Configuration block for VPC settings.

### Outputs

- `arn` (str) - Amazon Resource Name (ARN) identifying your Lambda Function.
- `code_sha256` (str) - Base64-encoded representation of raw SHA-256 sum of the zip file.
- `id` (str) - The provider-assigned unique ID for this managed resource.
- `invoke_arn` (str) - ARN to be used for invoking Lambda Function from API Gateway.
- `last_modified` (str) - Date this resource was last modified.
- `qualified_arn` (str) - ARN identifying your Lambda Function Version (if versioning is enabled).
- `qualified_invoke_arn` (str) - Qualified ARN (ARN with lambda version number) for invoking Lambda Function.
- `signing_job_arn` (str) - ARN of the signing job.
- `signing_profile_version_arn` (str) - ARN of the signing profile version.
- `source_code_size` (int) - Size in bytes of the function .zip file.
- `version` (str) - Latest published version of your Lambda Function.

## Import

Lambda Functions can be imported using the `function_name`:

```sh
$ pulumi import aws:lambda/function:Function test_lambda my_test_lambda_function
```