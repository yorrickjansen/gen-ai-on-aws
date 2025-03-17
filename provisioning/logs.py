import pulumi_aws as aws


def create_log_groups(stack_name, lambda_func, worker_lambda=None):
    """
    Creates explicitly defined CloudWatch Log Groups with retention policies.

    Args:
        stack_name: The name of the Pulumi stack
        lambda_func: API Lambda function resource
        worker_lambda: Worker Lambda function resource (optional)

    Returns:
        Dictionary of created log group resources
    """
    resources = {}

    # Define log retention period in days
    retention_days = 30

    # Create API Lambda log group using .apply() to handle the Output
    api_lambda_log_group = aws.cloudwatch.LogGroup(
        "api-lambda-log-group",
        name=lambda_func.name.apply(lambda name: f"/aws/lambda/{name}"),
        retention_in_days=retention_days,
        tags={
            "Name": f"{stack_name}-api-lambda-logs",
            "Environment": stack_name,
        },
    )
    resources["api_lambda_log_group"] = api_lambda_log_group

    # Create Worker Lambda log group if worker lambda exists
    if worker_lambda:
        worker_lambda_log_group = aws.cloudwatch.LogGroup(
            "worker-lambda-log-group",
            name=worker_lambda.name.apply(lambda name: f"/aws/lambda/{name}"),
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
