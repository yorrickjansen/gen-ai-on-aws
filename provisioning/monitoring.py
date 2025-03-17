import json

import pulumi
import pulumi_aws as aws


def create_monitoring_resources(
    stack_name,
    region,
    lambda_func,
    worker_lambda,
    sqs_queue,
    dlq,
    http_endpoint,
    http_stage,
    monitoring_email=None,
):
    """
    Creates CloudWatch alarms, dashboard, and optionally an SNS topic for monitoring the application.

    Args:
        stack_name: The name of the Pulumi stack
        region: AWS region
        lambda_func: API Lambda function resource
        worker_lambda: Worker Lambda function resource
        sqs_queue: Main SQS queue resource
        dlq: Dead Letter Queue resource
        http_endpoint: API Gateway endpoint resource
        http_stage: API Gateway stage resource
        monitoring_email: Optional email for notifications

    Returns:
        A dictionary containing created monitoring resources
    """
    resources = {}

    # Create an SNS topic for alerts if monitoring_email is provided
    alert_topic = None

    if monitoring_email:
        alert_topic = aws.sns.Topic(
            "alert-topic",
            name=f"{stack_name}-alerts",
            tags={
                "Name": f"{stack_name}-alerts",
                "Environment": stack_name,
            },
        )

        # Add email subscription
        email_subscription = aws.sns.TopicSubscription(
            "email-subscription",
            topic=alert_topic.arn,
            protocol="email",
            endpoint=monitoring_email,
        )

        resources["alert_topic"] = alert_topic
        resources["email_subscription"] = email_subscription

    # Prepare alarm actions list
    alarm_actions = []
    ok_actions = []
    if alert_topic:
        alarm_actions.append(alert_topic.arn)
        ok_actions.append(alert_topic.arn)

    # Lambda API errors alarm
    api_lambda_errors_alarm = aws.cloudwatch.MetricAlarm(
        "api-lambda-errors-alarm",
        name=f"{stack_name}-api-lambda-errors",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=1,
        metric_name="Errors",
        namespace="AWS/Lambda",
        period=60,
        statistic="Sum",
        threshold=0,
        alarm_description="Alarm for API Lambda errors",
        dimensions={
            "FunctionName": lambda_func.name,
        },
        alarm_actions=alarm_actions,
        ok_actions=ok_actions,
    )
    resources["api_lambda_errors_alarm"] = api_lambda_errors_alarm

    # Worker Lambda errors alarm
    if worker_lambda:
        worker_lambda_errors_alarm = aws.cloudwatch.MetricAlarm(
            "worker-lambda-errors-alarm",
            name=f"{stack_name}-worker-lambda-errors",
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=1,
            metric_name="Errors",
            namespace="AWS/Lambda",
            period=60,
            statistic="Sum",
            threshold=0,
            alarm_description="Alarm for Worker Lambda errors",
            dimensions={
                "FunctionName": worker_lambda.name,
            },
            alarm_actions=alarm_actions,
            ok_actions=ok_actions,
        )
        resources["worker_lambda_errors_alarm"] = worker_lambda_errors_alarm

        # Worker Lambda throttles alarm
        worker_lambda_throttles_alarm = aws.cloudwatch.MetricAlarm(
            "worker-lambda-throttles-alarm",
            name=f"{stack_name}-worker-lambda-throttles",
            comparison_operator="GreaterThanThreshold",
            evaluation_periods=1,
            metric_name="Throttles",
            namespace="AWS/Lambda",
            period=60,
            statistic="Sum",
            threshold=0,
            alarm_description="Alarm for Worker Lambda throttles",
            dimensions={
                "FunctionName": worker_lambda.name,
            },
            alarm_actions=alarm_actions,
            ok_actions=ok_actions,
        )
        resources["worker_lambda_throttles_alarm"] = worker_lambda_throttles_alarm

    # SQS DLQ message count alarm
    dlq_messages_alarm = aws.cloudwatch.MetricAlarm(
        "dlq-messages-alarm",
        name=f"{stack_name}-dlq-messages",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=1,
        metric_name="ApproximateNumberOfMessagesVisible",
        namespace="AWS/SQS",
        period=300,
        statistic="Maximum",
        threshold=0,
        alarm_description="Alarm when messages are in the Dead Letter Queue",
        dimensions={
            "QueueName": dlq.name,
        },
        alarm_actions=alarm_actions,
        ok_actions=ok_actions,
    )
    resources["dlq_messages_alarm"] = dlq_messages_alarm

    # API Gateway 5XX errors alarm
    api_gateway_5xx_alarm = aws.cloudwatch.MetricAlarm(
        "api-gateway-5xx-alarm",
        name=f"{stack_name}-api-gateway-5xx",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=1,
        metric_name="5XXError",
        namespace="AWS/ApiGateway",
        period=60,
        statistic="Sum",
        threshold=0,
        alarm_description="Alarm for API Gateway 5XX errors",
        dimensions={
            "ApiId": http_endpoint.id,
            "Stage": http_stage.name,
        },
        alarm_actions=alarm_actions,
        ok_actions=ok_actions,
    )
    resources["api_gateway_5xx_alarm"] = api_gateway_5xx_alarm

    # API Gateway 4XX errors alarm (optional - but useful to track client errors)
    api_gateway_4xx_alarm = aws.cloudwatch.MetricAlarm(
        "api-gateway-4xx-alarm",
        name=f"{stack_name}-api-gateway-4xx",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=1,
        metric_name="4XXError",
        namespace="AWS/ApiGateway",
        period=60,
        statistic="Sum",
        threshold=5,  # Allow a few 4XX errors as these are likely client errors
        alarm_description="Alarm for high number of API Gateway 4XX errors",
        dimensions={
            "ApiId": http_endpoint.id,
            "Stage": http_stage.name,
        },
        alarm_actions=alarm_actions,
        ok_actions=ok_actions,
    )
    resources["api_gateway_4xx_alarm"] = api_gateway_4xx_alarm

    # SQS queue message age alarm (detect stuck messages)
    sqs_message_age_alarm = aws.cloudwatch.MetricAlarm(
        "sqs-message-age-alarm",
        name=f"{stack_name}-sqs-message-age",
        comparison_operator="GreaterThanThreshold",
        evaluation_periods=1,
        metric_name="ApproximateAgeOfOldestMessage",
        namespace="AWS/SQS",
        period=300,
        statistic="Maximum",
        threshold=300,  # 5 minutes - same as visibility timeout
        alarm_description="Alarm when messages in the queue are not being processed",
        dimensions={
            "QueueName": sqs_queue.name,
        },
        alarm_actions=alarm_actions,
        ok_actions=ok_actions,
    )
    resources["sqs_message_age_alarm"] = sqs_message_age_alarm

    # Create a CloudWatch Dashboard for all metrics
    dashboard_widgets = []

    # Lambda API widget
    dashboard_widgets.append(
        {
            "type": "metric",
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/Lambda", "Errors", "FunctionName", lambda_func.name],
                    ["AWS/Lambda", "Invocations", "FunctionName", lambda_func.name],
                    [
                        "AWS/Lambda",
                        "Duration",
                        "FunctionName",
                        lambda_func.name,
                        {"stat": "Average"},
                    ],
                    [
                        "AWS/Lambda",
                        "Duration",
                        "FunctionName",
                        lambda_func.name,
                        {"stat": "Maximum"},
                    ],
                    ["AWS/Lambda", "Throttles", "FunctionName", lambda_func.name],
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": region,
                "title": "API Lambda Metrics",
                "period": 60,
            },
        }
    )

    # Worker Lambda widget (if it exists)
    if worker_lambda:
        dashboard_widgets.append(
            {
                "type": "metric",
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Errors", "FunctionName", worker_lambda.name],
                        [
                            "AWS/Lambda",
                            "Invocations",
                            "FunctionName",
                            worker_lambda.name,
                        ],
                        [
                            "AWS/Lambda",
                            "Duration",
                            "FunctionName",
                            worker_lambda.name,
                            {"stat": "Average"},
                        ],
                        [
                            "AWS/Lambda",
                            "Duration",
                            "FunctionName",
                            worker_lambda.name,
                            {"stat": "Maximum"},
                        ],
                        ["AWS/Lambda", "Throttles", "FunctionName", worker_lambda.name],
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": region,
                    "title": "Worker Lambda Metrics",
                    "period": 60,
                },
            }
        )

    # SQS Queue widget
    dashboard_widgets.append(
        {
            "type": "metric",
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [
                        "AWS/SQS",
                        "ApproximateNumberOfMessagesVisible",
                        "QueueName",
                        sqs_queue.name,
                    ],
                    [
                        "AWS/SQS",
                        "ApproximateAgeOfOldestMessage",
                        "QueueName",
                        sqs_queue.name,
                    ],
                    ["AWS/SQS", "NumberOfMessagesSent", "QueueName", sqs_queue.name],
                    [
                        "AWS/SQS",
                        "NumberOfMessagesReceived",
                        "QueueName",
                        sqs_queue.name,
                    ],
                    ["AWS/SQS", "NumberOfMessagesDeleted", "QueueName", sqs_queue.name],
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": region,
                "title": "SQS Queue Metrics",
                "period": 60,
            },
        }
    )

    # DLQ widget
    dashboard_widgets.append(
        {
            "type": "metric",
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [
                        "AWS/SQS",
                        "ApproximateNumberOfMessagesVisible",
                        "QueueName",
                        dlq.name,
                    ],
                    ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", dlq.name],
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": region,
                "title": "Dead Letter Queue Metrics",
                "period": 60,
            },
        }
    )

    # API Gateway widget
    dashboard_widgets.append(
        {
            "type": "metric",
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    [
                        "AWS/ApiGateway",
                        "Count",
                        "ApiId",
                        http_endpoint.id,
                        "Stage",
                        http_stage.name,
                    ],
                    [
                        "AWS/ApiGateway",
                        "4XXError",
                        "ApiId",
                        http_endpoint.id,
                        "Stage",
                        http_stage.name,
                    ],
                    [
                        "AWS/ApiGateway",
                        "5XXError",
                        "ApiId",
                        http_endpoint.id,
                        "Stage",
                        http_stage.name,
                    ],
                    [
                        "AWS/ApiGateway",
                        "Latency",
                        "ApiId",
                        http_endpoint.id,
                        "Stage",
                        http_stage.name,
                        {"stat": "Average"},
                    ],
                    [
                        "AWS/ApiGateway",
                        "Latency",
                        "ApiId",
                        http_endpoint.id,
                        "Stage",
                        http_stage.name,
                        {"stat": "p90"},
                    ],
                ],
                "view": "timeSeries",
                "stacked": False,
                "region": region,
                "title": "API Gateway Metrics",
                "period": 60,
            },
        }
    )

    # Create the CloudWatch Dashboard
    dashboard = aws.cloudwatch.Dashboard(
        "monitoring-dashboard",
        dashboard_name=f"{stack_name}-monitoring",
        dashboard_body=pulumi.Output.all(dashboard_widgets=dashboard_widgets).apply(
            lambda args: json.dumps({"widgets": args["dashboard_widgets"]})
        ),
    )
    resources["dashboard"] = dashboard

    # Calculate dashboard URL
    dashboard_url = pulumi.Output.concat(
        "https://",
        region,
        ".console.aws.amazon.com/cloudwatch/home?region=",
        region,
        "#dashboards:name=",
        dashboard.dashboard_name,
    )

    return resources, dashboard_url
