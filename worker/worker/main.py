import json
import logging
import os
from typing import Any

from worker.models.queue import QueueMessage
from worker.services.processor import Processor

# Get logging level from environment variable or default to INFO
log_level_name = os.environ.get("LOGGING_LEVEL", "INFO")
log_level = getattr(logging, log_level_name.upper(), logging.INFO)

logger = logging.getLogger()
logger.setLevel(log_level)

# Set specific level for litellm to reduce noise
logging.getLogger("litellm").setLevel(logging.WARNING)

processor = Processor()


async def process_message(message_body: str) -> dict[str, Any]:
    """Process a message from the SQS queue.

    Args:
        message_body: The body of the SQS message as a string

    Returns:
        Dict[str, Any]: The result of processing the message
    """
    try:
        queue_message = QueueMessage.model_validate_json(message_body)
        logger.info(f"Processing message with request ID: {queue_message.request_id}")

        result = await processor.process_extract_user_request(
            request=queue_message.payload, request_id=queue_message.request_id
        )

        return {
            "request_id": queue_message.request_id,
            "result": result.model_dump() if result else None,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {"error": str(e), "success": False}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda handler function.

    Args:
        event: The event data from AWS Lambda
        context: The runtime information from AWS Lambda

    Returns:
        Dict[str, Any]: The result of processing the messages
    """
    import asyncio

    logger.info(f"Received event: {json.dumps(event)}")

    results = []

    # Process each record (message) in the event
    for record in event.get("Records", []):
        message_body = record.get("body", "{}")
        result = asyncio.run(process_message(message_body))
        results.append(result)

    result = {"statusCode": 200, "body": json.dumps({"results": results})}

    logger.info(f"Processed {len(results)} messages")
    logger.info(f"Results: {json.dumps(result)}")

    return result
