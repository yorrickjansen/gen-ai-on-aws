import os

import httpx
import instructor
from fastapi import APIRouter, Depends, HTTPException
from langfuse.decorators import langfuse_context, observe
from litellm import completion
from loguru import logger

from gen_ai_on_aws.auth import verify_webhook_auth
from gen_ai_on_aws.config import VERSION, settings
from gen_ai_on_aws.endpoints.types import (
    ElevenLabsWebhookPayload,
    ElevenLabsWebhookResponse,
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


@router.post("/elevenlabs-webhook")
async def elevenlabs_webhook(
    payload: ElevenLabsWebhookPayload,
    supabase_config: tuple[str, str] = Depends(get_supabase_config),
    auth: str = Depends(verify_webhook_auth),
) -> ElevenLabsWebhookResponse:
    """Handle 11Labs conversation initiation webhook.

    This endpoint:
    1. Validates the auth header (via dependency)
    2. Checks blacklisted numbers
    3. Fetches client configuration from Supabase
    4. Returns dynamic variables for the conversation

    Args:
        payload: The webhook payload from 11Labs
        supabase_config: Supabase URL and key from dependency
        auth: The authenticated header value (validated by dependency)

    Returns:
        ElevenLabsWebhookResponse with dynamic variables

    Raises:
        HTTPException: For auth failures or missing data
    """
    logger.info(f"Processing 11Labs webhook for conversation {payload.conversation_id}")

    # Check blacklisted numbers (scammers)
    blacklisted_numbers = ["+41793000161", "+491787169629"]
    if payload.caller_id in blacklisted_numbers:
        logger.warning(f"Blocked blacklisted number: {payload.caller_id}")
        return ElevenLabsWebhookResponse(dynamic_variables={"error": "Number blocked"})

    # Fetch location data from Supabase
    supabase_url, supabase_key = supabase_config

    try:
        # Query for location data with phone number and account info
        url = f"{supabase_url}/rest/v1/onboarding_data"
        # Complex join query to fetch all related data
        select_query = (
            "*,"
            "phone_number!inner("
            "*,aura_account!inner(*),"
            "agent_version!left(*,agent!inner(*))"
            "),"
            "hotel_restaurants!left(*),"
            "closure_periods!left(*)"
        )
        params = {
            "select": select_query,
            "phone_number.phone_number": f"eq.{payload.called_number}",
        }
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

        locations_data = response.json()

        if not locations_data:
            logger.warning(f"No configuration found for number: {payload.called_number}")
            return ElevenLabsWebhookResponse(
                dynamic_variables={"error": "Could not find client configuration"}
            )

        # Process the data (simplified version of the n8n logic)
        first_location = locations_data[0]
        phone_number_config = first_location.get("phone_number", {})
        account = phone_number_config.get("aura_account", {})
        agent_config = phone_number_config.get("agent_config", {})

        # Format phone number
        formatted_phone_number = _format_phone_number(payload.caller_id)

        # Determine if phone can receive SMS (simplified)
        can_receive_sms = _can_receive_sms(payload.caller_id)

        # Build dynamic variables (matching the n8n structure)
        dynamic_variables = {
            "host_name": account.get("name", ""),
            "test_account": str(account.get("test_account", False)),
            "mode": "single-location" if len(locations_data) == 1 else "multi-location",
            "hotel_category": account.get("hotel_category", ""),
            "preferred_currency": account.get("preferred_currency", "EUR"),
            "welcomeMessage": agent_config.get("welcomeMessage", ""),
            "agent_name": agent_config.get("agentName", ""),
            "formOfAddress": agent_config.get("formOfAddress", "Formal"),
            "formatted_user_number": formatted_phone_number,
            "last_two_digits": formatted_phone_number[-2:]
            if len(formatted_phone_number) >= 2
            else "",
            "can_phone_number_receive_sms_details": "User phone number CAN receive SMS"
            if can_receive_sms
            else "User phone number CANNOT receive SMS",
            "location_details": _serialize_locations(locations_data),
        }

        logger.info(f"Successfully processed webhook for {account.get('name', 'Unknown')}")

        return ElevenLabsWebhookResponse(dynamic_variables=dynamic_variables)

    except httpx.HTTPStatusError as e:
        logger.error(f"Supabase error: {e}")
        return ElevenLabsWebhookResponse(
            dynamic_variables={"error": "Failed to fetch configuration"}
        )
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        return ElevenLabsWebhookResponse(dynamic_variables={"error": "Internal processing error"})


def _format_phone_number(phone_number: str) -> str:
    """Format a phone number for display.

    Args:
        phone_number: The raw phone number

    Returns:
        Formatted phone number with separators
    """
    if not phone_number or phone_number == "Anonymous":
        return "Anonymous"

    # Remove any non-digit characters except +
    cleaned = "".join(c for c in phone_number if c.isdigit() or c == "+")

    if not cleaned:
        return phone_number

    # Handle US/Canada numbers (+1 followed by 10 digits)
    if cleaned.startswith("+1") and len(cleaned) == 12:
        return f"+1 - {cleaned[2:5]} - {cleaned[5:8]} - {cleaned[8:]}"

    # Handle German numbers (+49)
    if cleaned.startswith("+49"):
        country_code = cleaned[:3]
        remaining = cleaned[3:]
        # Format remaining digits in groups of 3
        groups = []
        for i in range(0, len(remaining), 3):
            groups.append(remaining[i : i + 3])
        return f"{country_code} - " + " - ".join(groups)

    # Default formatting for other numbers
    return phone_number


def _can_receive_sms(phone_number: str) -> bool:
    """Determine if a phone number can receive SMS.

    Args:
        phone_number: The phone number to check

    Returns:
        True if the number can receive SMS, False otherwise
    """
    if not phone_number or phone_number == "Anonymous":
        return False

    # German mobile numbers check
    if phone_number.startswith("+49"):
        # German mobile numbers use 15x, 16x, 17x prefixes
        after_country = phone_number[3:]
        if (
            len(after_country) >= 2
            and after_country[0] == "1"
            and after_country[1] in ("5", "6", "7")
        ):
            return True
        return False

    # Assume other numbers can receive SMS
    return True


def _serialize_locations(locations_data: list) -> str:
    """Serialize location data for dynamic variables.

    Args:
        locations_data: List of location data from Supabase

    Returns:
        JSON string of location details
    """
    import json

    # Remove sensitive data and format for AI agent
    locations = []
    for loc in locations_data:
        location = {
            "location_id": loc.get("id"),
            "location_name": loc.get("location_name"),
            "check_in_support_type": loc.get("check_in_support_type", "not_specified"),
            "website_url": loc.get("website_url", "not_specified"),
            "contact_email": loc.get("contact_email", "not_specified"),
        }
        locations.append(location)

    return json.dumps(locations, separators=(",", ":"))
