# Monitoring and Alerting for Gen-AI-on-AWS

This document outlines the monitoring and alerting setup for the Gen-AI-on-AWS application.

## Overview

The monitoring system is designed to detect and alert on issues across all components of the application:

1. API Lambda function errors
2. Worker Lambda function errors and throttles
3. SQS queue health and Dead Letter Queue (DLQ) messages
4. API Gateway 5XX and 4XX errors

## Monitoring Components

### CloudWatch Alarms

The following CloudWatch Alarms are configured:

| Alarm Name | Resource | Metric | Threshold | Description |
|------------|----------|--------|-----------|-------------|
| api-lambda-errors | API Lambda | Errors | >0 | Alerts when any errors occur in the API Lambda |
| worker-lambda-errors | Worker Lambda | Errors | >0 | Alerts when any errors occur in the Worker Lambda |
| worker-lambda-throttles | Worker Lambda | Throttles | >0 | Alerts when the Worker Lambda is being throttled |
| dlq-messages | Dead Letter Queue | ApproximateNumberOfMessagesVisible | >0 | Alerts when any messages appear in the DLQ |
| sqs-message-age | SQS Queue | ApproximateAgeOfOldestMessage | >300 seconds | Alerts when messages are not being processed in time |
| api-gateway-5xx | API Gateway | 5XXError | >0 | Alerts when 5XX errors occur in the API Gateway |
| api-gateway-4xx | API Gateway | 4XXError | >5 | Alerts when a significant number of 4XX client errors occur |

### CloudWatch Dashboard

A comprehensive dashboard is provided at the URL output by Pulumi (`dashboard_url`). The dashboard includes:

1. **API Lambda Metrics**:
   - Errors, Invocations, Duration (Average & Maximum), Throttles

2. **Worker Lambda Metrics**:
   - Errors, Invocations, Duration (Average & Maximum), Throttles

3. **SQS Queue Metrics**:
   - Message count, Age of oldest message, Message send/receive/delete rates

4. **Dead Letter Queue Metrics**:
   - Message count, Age of oldest message

5. **API Gateway Metrics**:
   - Request count, 4XX errors, 5XX errors, Latency (Average & p90)

## Notifications

Notifications can be enabled by setting the `monitoring_email` configuration value in your Pulumi config file:

```yaml
# In Pulumi.dev.yaml or Pulumi.demo.yaml
config:
  # ...other config values...
  monitoring_email: your.email@example.com
```

When an email is provided, an SNS topic is created and all alarms will send notifications to this email address when they enter ALARM state and when they return to OK state.

## Dead Letter Queue (DLQ)

The SQS queue is configured with a Dead Letter Queue that captures messages after 3 failed processing attempts. This helps identify issues with message processing and prevents infinite retries of problematic messages.

You can view the DLQ URL in the Pulumi outputs (`dlq_url`) and can monitor it through:

1. The CloudWatch Dashboard
2. The DLQ CloudWatch Alarm
3. The AWS SQS Console

## Troubleshooting Guide

When alerts fire:

1. **Lambda Errors**:
   - Check CloudWatch Logs for the specific Lambda function
   - Look for stack traces or error messages
   - Check for resource limitations or timeouts

2. **DLQ Messages**:
   - Examine messages in the DLQ through the AWS Console
   - Look for patterns in failed messages
   - Check CloudWatch Logs for the worker lambda to see processing errors

3. **API Gateway 5XX Errors**:
   - Check API Lambda logs for server-side errors
   - Look for integration issues between API Gateway and Lambda
   - Check for Lambda timeouts or memory issues

4. **Message Age Alerts**:
   - Check if the worker Lambda is running
   - Look for Lambda throttling or concurrency issues
   - Check for high volume of messages overwhelming the worker