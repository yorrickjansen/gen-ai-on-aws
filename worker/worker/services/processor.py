import logging
from typing import Optional

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
        self, request: ExtractUserRequest
    ) -> User | None:
        """Process a request to extract user information from text.

        Args:
            request: The request containing the text to extract user information from

        Returns:
            User | None: The extracted user information, or None if no valid user information was found
        """
        logger.info(f"Processing request to extract user from text: {request.text}")
        langfuse_context.update_current_trace(metadata={"app_version": VERSION})

        try:
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
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return None
