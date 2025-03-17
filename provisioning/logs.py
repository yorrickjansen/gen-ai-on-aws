import pulumi
import pulumi_aws as aws


def create_log_groups(stack_name, api_function_name, worker_function_name=None):
    """
    Creates explicitly defined CloudWatch Log Groups with retention policies.

    Args:
        stack_name: The name of the Pulumi stack
        api_function_name: API Lambda function name (string, not an Output)
        worker_function_name: Worker Lambda function name (string, not an Output) (optional)

    Returns:
        Dictionary of created log group resources
    """
    resources = {}

    # Define log retention period in days
    retention_days = 30

    # Create API Lambda log group - using a string directly now
    api_lambda_log_group = aws.cloudwatch.LogGroup(
        "api-lambda-log-group",
        name=f"/aws/lambda/{api_function_name}",
        retention_in_days=retention_days,
        tags={
            "Name": f"{stack_name}-api-lambda-logs",
            "Environment": stack_name,
        },
    )
    resources["api_lambda_log_group"] = api_lambda_log_group

    # Create Worker Lambda log group if worker lambda name is provided
    if worker_function_name:
        worker_lambda_log_group = aws.cloudwatch.LogGroup(
            "worker-lambda-log-group",
            name=f"/aws/lambda/{worker_function_name}",
            retention_in_days=retention_days,
            tags={
                "Name": f"{stack_name}-worker-lambda-logs",
                "Environment": stack_name,
            },
        )
        resources["worker_lambda_log_group"] = worker_lambda_log_group

    # Create API Gateway log group
    api_gateway_log_group = aws.cloudwatch.LogGroup(
        "api-gateway-log-group",
        name=f"API-Gateway-Execution-Logs_{stack_name}",
        retention_in_days=retention_days,
        tags={
            "Name": f"{stack_name}-api-gateway-logs",
            "Environment": stack_name,
        },
    )
    resources["api_gateway_log_group"] = api_gateway_log_group

    return resources


def get_logging_level():
    """
    Get logging level from Pulumi config or return default.

    Returns:
        str: Logging level (INFO, DEBUG, WARNING, ERROR, or CRITICAL)
    """
    config = pulumi.Config()
    return config.get("logging_level", "INFO")
