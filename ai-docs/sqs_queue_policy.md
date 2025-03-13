# AWS SQS Queue Policy

The AWS SQS Queue Policy resource allows you to set a policy for an SQS Queue while referencing the ARN of the queue within the policy.

## Important Note

AWS will hang indefinitely when creating or updating an `aws.sqs.Queue` with an associated policy if `Version = "2012-10-17"` is not explicitly set in the policy. Always include the Version parameter to avoid timeout issues.

## Example Usage

### Basic Example

```python
import pulumi
import pulumi_aws as aws

# Create the SQS queue
queue = aws.sqs.Queue("myQueue", name="example-queue")

# Create a policy document
policy_document = queue.arn.apply(lambda arn: aws.iam.get_policy_document_output(statements=[{
    "sid": "AllowSendMessage",
    "effect": "Allow",
    "principals": [{
        "type": "*",
        "identifiers": ["*"],
    }],
    "actions": ["sqs:SendMessage"],
    "resources": [arn],
    "conditions": [{
        "test": "ArnEquals",
        "variable": "aws:SourceArn",
        "values": [example_resource.arn],
    }],
}]))

# Attach the policy to the queue
queue_policy = aws.sqs.QueuePolicy("queuePolicy",
    queue_url=queue.id,
    policy=policy_document.json)
```

### Avoiding Timeout Issues

Always explicitly include the `Version` field in your policy to avoid AWS hanging indefinitely:

```python
import pulumi
import json
import pulumi_aws as aws

# Create the queue
queue = aws.sqs.Queue("exampleQueue", name="example-queue")

# Create the policy with explicit Version field
queue_policy = aws.sqs.QueuePolicy("examplePolicy",
    queue_url=queue.id,
    policy=pulumi.Output.json_dumps({
        "Version": "2012-10-17",  # Always include this
        "Statement": [{
            "Sid": "AllowS3",
            "Effect": "Allow",
            "Principal": {
                "Service": "s3.amazonaws.com"
            },
            "Action": "SQS:SendMessage",
            "Resource": queue.arn,
            "Condition": {
                "ArnLike": {
                    "aws:SourceArn": source_bucket.arn
                }
            }
        }]
    }))
```

## Resource Properties

### Inputs

| Property | Type | Description |
|----------|------|-------------|
| policy | str | The JSON policy for the SQS queue. Must include `Version = "2012-10-17"` to avoid timeout issues |
| queue_url | str | URL of the SQS Queue to which to attach the policy |

### Outputs

| Property | Type | Description |
|----------|------|-------------|
| id | str | The provider-assigned unique ID for this managed resource |

## Import

SQS Queue Policies can be imported using the queue URL:

```
$ pulumi import aws:sqs/queuePolicy:QueuePolicy test https://queue.amazonaws.com/123456789012/myqueue
```