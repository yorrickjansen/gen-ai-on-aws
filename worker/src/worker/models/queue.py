from typing import Optional
from pydantic import BaseModel, Field

class ExtractUserRequest(BaseModel):
    """Request to extract user information from text."""
    text: str = Field(description="The text to extract user information from.")


class User(BaseModel):
    """User information extracted from text."""
    name: str = Field(description="The name of the user.")
    age: int = Field(description="The age of the user.")
    email: Optional[str] = Field(description="The email of the user.", default=None)


class QueueMessage(BaseModel):
    """Message received from the SQS queue."""
    request_id: str = Field(description="Unique identifier for the request")
    payload: ExtractUserRequest = Field(description="The request payload to be processed")