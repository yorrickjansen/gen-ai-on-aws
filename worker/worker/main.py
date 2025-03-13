import json
import logging
from typing import Any, Dict

from worker.models.queue import QueueMessage
from worker.services.processor import Processor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

processor = Processor()


async def process_message(message_body: str) -> Dict[str, Any]:
    """Process a message from the SQS queue.

    Args:
        message_body: The body of the SQS message as a string

    Returns:
        Dict[str, Any]: The result of processing the message
    """
    try:
        queue_message = QueueMessage.model_validate_json(message_body)
        logger.info(f"Processing message with request ID: {queue_message.request_id}")

        result = await processor.process_extract_user_request(queue_message.payload)

        return {
            "request_id": queue_message.request_id,
            "result": result.model_dump() if result else None,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return {"error": str(e), "success": False}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
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

    return {"statusCode": 200, "body": json.dumps({"results": results})}
