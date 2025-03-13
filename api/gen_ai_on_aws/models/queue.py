from gen_ai_on_aws.examples.types import ExtractUserRequest
from pydantic import BaseModel, Field


class QueueMessage(BaseModel):
    """Message to be sent to the SQS queue."""

    request_id: str = Field(description="Unique identifier for the request")
    payload: ExtractUserRequest = Field(
        description="The request payload to be processed"
    )
