# AWS Lambda EventSourceMapping

The Lambda EventSourceMapping resource creates a mapping between an event source and an AWS Lambda function. It enables automatic invocation of a Lambda function when events occur in the specified source.

## Key Features

- Maps event sources to Lambda functions
- Supports various event sources: Kinesis, DynamoDB, SQS, MSK, DocumentDB, MQ, and self-managed Kafka
- Configurable batch sizes and processing windows
- Filtering capabilities for event processing
- Error handling with retries and failure destinations
- Scalability options for concurrent processing

## Python Example: SQS to Lambda

```python
import pulumi
import pulumi_aws as aws

# Create an SQS queue
queue = aws.sqs.Queue("myQueue")

# Create a Lambda function to process messages
function = aws.lambda_.Function("myFunction",
    runtime="python3.9",
    code=pulumi.FileArchive("./lambda_code.zip"),
    handler="index.handler",
    role=lambda_role.arn)

# Create the event source mapping
event_source_mapping = aws.lambda_.EventSourceMapping("myEventSourceMapping",
    event_source_arn=queue.arn,
    function_name=function.arn,
    batch_size=10,
    maximum_batching_window_in_seconds=30)
```

## Common Parameters

| Parameter | Description |
|-----------|-------------|
| `function_name` | Name or ARN of the Lambda function |
| `event_source_arn` | ARN of the event source (required for Kinesis, DynamoDB, SQS, MQ, MSK, DocumentDB) |
| `enabled` | Whether the mapping is enabled (default: true) |
| `batch_size` | Maximum number of records in each batch (default: 100 for streams, 10 for SQS) |
| `maximum_batching_window_in_seconds` | Maximum time to gather records before invoking function (0-300 seconds) |
| `starting_position` | Position to start reading from streams (`LATEST`, `TRIM_HORIZON`, or `AT_TIMESTAMP`) |
| `filter_criteria` | Criteria for filtering events before processing |

## Filter Criteria

You can filter events before they reach your Lambda function:

```python
event_source_mapping = aws.lambda_.EventSourceMapping("myEventSourceMapping",
    event_source_arn=queue.arn,
    function_name=function.name,
    filter_criteria={
        "filters": [{
            "pattern": json.dumps({
                "body": {
                    "messageType": ["order"],
                    "priority": [{"numeric": [">", 50]}]
                }
            })
        }]
    })
```

## Error Handling

Configure error handling for your event source mapping:

```python
event_source_mapping = aws.lambda_.EventSourceMapping("myEventSourceMapping",
    event_source_arn=kinesis_stream.arn,
    function_name=function.name,
    starting_position="LATEST",
    bisect_batch_on_function_error=True,
    maximum_retry_attempts=10,
    destination_config={
        "on_failure": {
            "destination_arn": dead_letter_queue.arn
        }
    })
```

## Scaling and Performance

For SQS sources, control concurrency:

```python
event_source_mapping = aws.lambda_.EventSourceMapping("myEventSourceMapping",
    event_source_arn=queue.arn,
    function_name=function.name,
    scaling_config={
        "maximum_concurrency": 50
    })
```

For stream sources, control parallelization:

```python
event_source_mapping = aws.lambda_.EventSourceMapping("myEventSourceMapping",
    event_source_arn=kinesis_stream.arn,
    function_name=function.name,
    starting_position="LATEST",
    parallelization_factor=10)
```

## Important Considerations

1. Different event sources have different configuration requirements
2. For streams (Kinesis, DynamoDB), `starting_position` is required
3. For SQS, `starting_position` must not be provided
4. The Lambda function must have permissions to access the event source
5. Some event sources require additional configuration for security
