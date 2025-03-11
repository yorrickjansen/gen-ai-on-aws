# AWS SQS Queue

Amazon SQS (Simple Queue Service) is a fully managed message queuing service that enables decoupling and scaling of microservices, distributed systems, and serverless applications. This resource allows you to create, configure, and manage an SQS queue, which acts as a reliable message buffer between producers and consumers. With support for standard and FIFO queues, SQS ensures secure, scalable, and asynchronous message processing.

## Important Notes

- AWS will hang indefinitely, leading to a `timeout while waiting` error, when creating or updating an `aws.sqs.Queue` with an associated `aws.sqs.QueuePolicy` if `Version = "2012-10-17"` is not explicitly set in the policy.
- AWS will hang indefinitely and trigger a `timeout while waiting` error when creating or updating an `aws.sqs.Queue` if `kms_data_key_reuse_period_seconds` is set to a non-default value, `sqs_managed_sse_enabled` is `false` (explicitly or by default), and `kms_master_key_id` is not set.

## Example Usage

### Standard Queue

```python
import pulumi
import json
import pulumi_aws as aws

queue = aws.sqs.Queue("queue",
    name="example-queue",
    delay_seconds=90,
    max_message_size=2048,
    message_retention_seconds=86400,
    receive_wait_time_seconds=10,
    redrive_policy=json.dumps({
        "deadLetterTargetArn": queue_deadletter["arn"],
        "maxReceiveCount": 4,
    }),
    tags={
        "Environment": "production",
    })
```

### FIFO Queue

```python
import pulumi
import pulumi_aws as aws

queue = aws.sqs.Queue("queue",
    name="example-queue.fifo",
    fifo_queue=True,
    content_based_deduplication=True)
```

### High-throughput FIFO Queue

```python
import pulumi
import pulumi_aws as aws

queue = aws.sqs.Queue("queue",
    name="pulumi-example-queue.fifo",
    fifo_queue=True,
    deduplication_scope="messageGroup",
    fifo_throughput_limit="perMessageGroupId")
```

### Dead-letter Queue

```python
import pulumi
import json
import pulumi_aws as aws

queue = aws.sqs.Queue("queue",
    name="pulumi-example-queue",
    redrive_policy=json.dumps({
        "deadLetterTargetArn": queue_deadletter["arn"],
        "maxReceiveCount": 4,
    }))
example_queue_deadletter = aws.sqs.Queue("example_queue_deadletter", name="pulumi-example-deadletter-queue")
example_queue_redrive_allow_policy = aws.sqs.RedriveAllowPolicy("example_queue_redrive_allow_policy",
    queue_url=example_queue_deadletter.id,
    redrive_allow_policy=json.dumps({
        "redrivePermission": "byQueue",
        "sourceQueueArns": [example_queue["arn"]],
    }))
```

### Server-side Encryption (SSE)

#### Using SSE-SQS

```python
import pulumi
import pulumi_aws as aws

queue = aws.sqs.Queue("queue",
    name="pulumi-example-queue",
    sqs_managed_sse_enabled=True)
```

#### Using SSE-KMS

```python
import pulumi
import pulumi_aws as aws

queue = aws.sqs.Queue("queue",
    name="example-queue",
    kms_master_key_id="alias/aws/sqs",
    kms_data_key_reuse_period_seconds=300)
```

## Queue Resource Properties

### Inputs

| Property | Type | Description |
|----------|------|-------------|
| content_based_deduplication | bool | Enables content-based deduplication for FIFO queues |
| deduplication_scope | str | Specifies whether message deduplication occurs at the message group or queue level. Valid values are `messageGroup` and `queue` (default) |
| delay_seconds | int | Time in seconds that the delivery of all messages in the queue will be delayed. Default is 0 seconds (0-900) |
| fifo_queue | bool | Boolean designating a FIFO queue. If not set, it defaults to `false` making it standard |
| fifo_throughput_limit | str | Specifies FIFO queue throughput quota (`perQueue` or `perMessageGroupId`) |
| kms_data_key_reuse_period_seconds | int | Length of time for which Amazon SQS can reuse a data key for encryption. Default is 300 seconds (60-86400) |
| kms_master_key_id | str | ID of an AWS-managed customer master key (CMK) for Amazon SQS or a custom CMK |
| max_message_size | int | Maximum size of messages in bytes. Default is 262144 (1024-262144) |
| message_retention_seconds | int | Number of seconds Amazon SQS retains a message. Default is 345600 seconds (60-1209600) |
| name | str | Name of the queue (Required for FIFO queues to end with .fifo) |
| name_prefix | str | Creates a unique name beginning with the specified prefix |
| policy | str | JSON policy for the SQS queue |
| receive_wait_time_seconds | int | Time for which a ReceiveMessage call will wait for a message. Default is 0 seconds (0-20) |
| redrive_allow_policy | str | JSON policy to set up the Dead Letter Queue redrive permission |
| redrive_policy | str | JSON policy to set up the Dead Letter Queue |
| sqs_managed_sse_enabled | bool | Boolean to enable server-side encryption with SQS-owned encryption keys |
| tags | dict | Map of tags to assign to the queue |
| visibility_timeout_seconds | int | Visibility timeout for the queue. Default is 30 seconds (0-43200) |

### Outputs

| Property | Type | Description |
|----------|------|-------------|
| arn | str | ARN of the SQS queue |
| id | str | The provider-assigned unique ID for this managed resource |
| url | str | The URL for the created Amazon SQS queue (same as `id`) |

## Import

SQS Queues can be imported using the queue `url`:

```sh
$ pulumi import aws:sqs/queue:Queue public_queue https://queue.amazonaws.com/80398EXAMPLE/MyQueue
```