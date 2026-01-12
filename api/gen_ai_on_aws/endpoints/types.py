from typing import Any

from pydantic import BaseModel, Field


class ExtractUserRequest(BaseModel):
    """Request model for extracting user information from text."""

    text: str = Field(description="The text to extract user information from.")


class User(BaseModel):
    name: str = Field(description="The name of the user.")
    age: int = Field(description="The age of the user.")
    email: str | None = Field(description="The email of the user.", default=None)


class ExtractUserAsyncResponse(BaseModel):
    request_id: str = Field(description="Unique identifier for the async request")


class SupabaseReadRequest(BaseModel):
    table: str = Field(description="The name of the Supabase table to read from")
    select: str = Field(description="The columns to select (e.g., '*' or 'id,name')", default="*")
    limit: int | None = Field(description="Maximum number of rows to return", default=None)


class SupabaseReadResponse(BaseModel):
    data: list[Any] = Field(description="The data returned from Supabase")


class ElevenLabsWebhookPayload(BaseModel):
    """Request payload from 11Labs conversation initiation webhook."""

    caller_id: str = Field(description="The phone number of the caller")
    agent_id: str = Field(description="The ID of the 11Labs agent")
    called_number: str = Field(description="The number that was called")
    call_sid: str = Field(description="The unique call session ID")
    conversation_id: str = Field(description="The unique conversation ID")


class ElevenLabsWebhookResponse(BaseModel):
    """Response for 11Labs conversation initiation webhook."""

    dynamic_variables: dict[str, Any] = Field(
        description="Dynamic variables to inject into the agent conversation"
    )
