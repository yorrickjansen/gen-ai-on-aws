import logging
from typing import Optional

import instructor
from fastapi import APIRouter, Depends, HTTPException
from gen_ai_on_aws.config import VERSION, settings
from gen_ai_on_aws.examples.types import (
    ExtractUserAsyncResponse,
    ExtractUserRequest,
    User,
)
from gen_ai_on_aws.services.queue_service import QueueService
from langfuse.decorators import langfuse_context, observe
from litellm import completion

# Create instructor client using litellm
client = instructor.from_litellm(completion)


router = APIRouter()
logger = logging.getLogger(__name__)


def get_queue_service() -> QueueService:
    """Dependency to get the QueueService.

    Returns:
        QueueService: The initialized QueueService
    """
    if not settings.sqs_queue_url:
        raise HTTPException(status_code=500, detail="SQS queue URL not configured")
    return QueueService(queue_url=settings.sqs_queue_url)


@router.get("/hello")
async def root() -> str:
    return "Hello, world!"


@router.post("/extract-user")
@observe
async def extract_user(request: ExtractUserRequest) -> User | None:
    logger.info(f"Extracting user from text: {request.text}")
    langfuse_context.update_current_trace(metadata={"app_version": VERSION})

    response = client.chat.completions.create(
        model=settings.model,
        messages=[
            {
                "role": "system",
                "content": "Extract user information from the provided text. If no valid user information is found, return None. Only extract information if you're confident about the values.",
            },
            {
                "role": "user",
                "content": request.text,
            },
        ],
        response_model=Optional[User],
        # https://langfuse.com/docs/integrations/litellm/tracing#use-within-decorated-function
        metadata={
            "existing_trace_id": langfuse_context.get_current_trace_id(),  # set langfuse trace ID
            "parent_observation_id": langfuse_context.get_current_observation_id(),
        },
    )
    return response


@router.post("/extract-user-async")
@observe
async def extract_user_async(
    request: ExtractUserRequest,
    queue_service: QueueService = Depends(get_queue_service),
) -> ExtractUserAsyncResponse:
    """Send a request to extract user information to the queue for async processing.

    Args:
        request: The request containing the text to extract user information from
        queue_service: The QueueService to send the message to the queue

    Returns:
        ExtractUserAsyncResponse: Response containing the request ID for tracking
    """
    logger.info(f"Sending async request to extract user from text: {request.text}")
    langfuse_context.update_current_trace(metadata={"app_version": VERSION})

    request_id = queue_service.send_message(request)
    if not request_id:
        raise HTTPException(status_code=500, detail="Failed to send message to queue")

    # Add request_id to langfuse for traceability
    langfuse_context.update_current_trace(metadata={"request_id": request_id})

    return ExtractUserAsyncResponse(request_id=request_id)
