import os

import httpx
import instructor
from fastapi import APIRouter, Depends, HTTPException
from langfuse.decorators import langfuse_context, observe
from litellm import completion
from loguru import logger

from gen_ai_on_aws.config import VERSION, settings
from gen_ai_on_aws.endpoints.types import (
    ExtractUserAsyncResponse,
    ExtractUserRequest,
    SupabaseReadRequest,
    SupabaseReadResponse,
    User,
)
from gen_ai_on_aws.services.queue_service import QueueService

# Create instructor client using litellm
client = instructor.from_litellm(completion)


router = APIRouter()


def get_queue_service() -> QueueService:
    """Dependency to get the QueueService.

    Returns:
        QueueService: The initialized QueueService
    """
    if not settings.sqs_queue_url:
        raise HTTPException(status_code=500, detail="SQS queue URL not configured")
    return QueueService(queue_url=settings.sqs_queue_url)


def get_supabase_config() -> tuple[str, str]:
    """Dependency to get Supabase configuration.

    Returns:
        tuple[str, str]: Tuple of (supabase_url, supabase_key)

    Raises:
        HTTPException: If Supabase URL or key is not configured
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="Supabase URL and key must be configured in environment variables",
        )

    return supabase_url, supabase_key


@router.get("/hello")
async def root() -> str:
    return "Hello, world!"


@router.post("/extract-user")
@observe
async def extract_user(request: ExtractUserRequest) -> User | None:
    logger.info(f"Extracting user from text: {request.text}")
    langfuse_context.update_current_trace(metadata={"app_version": VERSION})

    response = client.chat.completions.create(  # type: ignore[call-overload]
        model=settings.model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract user information from the provided text. "
                    "If no valid user information is found, return None. "
                    "Only extract information if you're confident about the values."
                ),
            },
            {
                "role": "user",
                "content": request.text,
            },
        ],
        response_model=User,
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


@router.post("/supabase-read")
async def supabase_read(
    request: SupabaseReadRequest,
    supabase_config: tuple[str, str] = Depends(get_supabase_config),
) -> SupabaseReadResponse:
    """Read data from a Supabase table using the REST API.

    Args:
        request: The request containing table name, select columns, and optional limit
        supabase_config: Tuple of (supabase_url, supabase_key) from dependency

    Returns:
        SupabaseReadResponse: Response containing the data from Supabase

    Raises:
        HTTPException: If there's an error reading from Supabase
    """
    logger.info(f"Reading from Supabase table: {request.table}")
    supabase_url, supabase_key = supabase_config

    try:
        # Build the Supabase REST API URL
        url = f"{supabase_url}/rest/v1/{request.table}"

        # Build query parameters
        params = {"select": request.select}
        if request.limit:
            params["limit"] = str(request.limit)

        # Set up headers for Supabase REST API
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
        }

        # Make the HTTP request
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

        return SupabaseReadResponse(data=response.json())
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error reading from Supabase: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to read from Supabase: {e.response.text}",
        ) from e
    except Exception as e:
        logger.error(f"Error reading from Supabase: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to read from Supabase: {str(e)}"
        ) from e
