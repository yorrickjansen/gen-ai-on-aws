import json
import logging
import boto3
import uuid
from gen_ai_on_aws.models.queue import QueueMessage

logger = logging.getLogger(__name__)


class QueueService:
    def __init__(self, queue_url: str):
        """Initialize the QueueService with the SQS queue URL.

        Args:
            queue_url: The URL of the SQS queue
        """
        self.queue_url = queue_url
        self.sqs_client = boto3.client("sqs")

    async def send_message(self, payload) -> str:
        """Send a message to the SQS queue.

        Args:
            payload: The payload to be sent to the queue

        Returns:
            str: The message ID if successful, otherwise None
        """
        request_id = str(uuid.uuid4())
        message = QueueMessage(request_id=request_id, payload=payload)

        try:
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url, MessageBody=message.model_dump_json()
            )
            message_id = response.get("MessageId")
            logger.info(
                f"Message sent to SQS queue. Message ID: {message_id}, Request ID: {request_id}"
            )
            return request_id
        except Exception as e:
            logger.error(f"Error sending message to SQS queue: {e}")
            return None
