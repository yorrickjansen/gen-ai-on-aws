import logging

import instructor
from langfuse.decorators import langfuse_context, observe
from litellm import completion

from worker.config import VERSION, settings
from worker.models.queue import ExtractUserRequest, User

logger = logging.getLogger(__name__)

# Create instructor client using litellm
client = instructor.from_litellm(completion)


class Processor:
    """Processes messages from the SQS queue."""

    @observe
    async def process_extract_user_request(
        self, request: ExtractUserRequest, request_id: str | None = None
    ) -> User | None:
        """Process a request to extract user information from text.

        Args:
            request: The request containing the text to extract user information from
            request_id: The ID of the request for tracing

        Returns:
            User | None: The extracted user information, or None if no valid
                user information was found
        """
        logger.info(f"Processing request to extract user from text: {request.text}")

        # Update langfuse trace with metadata including request_id if available
        metadata = {"app_version": VERSION}
        if request_id:
            metadata["request_id"] = request_id
        langfuse_context.update_current_trace(metadata=metadata)

        try:
            response = client.chat.completions.create(  # pyright: ignore[reportCallIssue,reportArgumentType]
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
                response_model=User | None,  # pyright: ignore[reportArgumentType]
                # https://langfuse.com/docs/integrations/litellm/tracing#use-within-decorated-function
                metadata={
                    "existing_trace_id": langfuse_context.get_current_trace_id(),
                    "parent_observation_id": langfuse_context.get_current_observation_id(),
                    **({"request_id": request_id} if request_id else {}),
                },
            )
            return response
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return None
