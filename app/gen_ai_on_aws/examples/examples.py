from re import S
from typing import Optional

import instructor
import logging

from gen_ai_on_aws.examples.types import ExtractUserRequest, User
from langfuse.decorators import langfuse_context, observe
from litellm import completion

from fastapi import APIRouter
from gen_ai_on_aws.config import VERSION, MODEL

# Create instructor client using litellm
client = instructor.from_litellm(completion)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/hello")
async def root() -> str:
    return "Hello, world!"


@router.post("/extract-user")
@observe
async def extract_user(request: ExtractUserRequest) -> User | None:
    logger.info(f"Extracting user from text: {request.text}")
    langfuse_context.update_current_trace(metadata={"app_version": VERSION})

    response = client.chat.completions.create(
        model=MODEL,
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
