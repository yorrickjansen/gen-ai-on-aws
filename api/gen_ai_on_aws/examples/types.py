from typing import Optional

from pydantic import BaseModel, Field


class ExtractUserRequest(BaseModel):
    text: str = Field(description="The text to extract user information from.")


class User(BaseModel):
    name: str = Field(description="The name of the user.")
    age: int = Field(description="The age of the user.")
    email: Optional[str] = Field(description="The email of the user.", default=None)


class ExtractUserAsyncResponse(BaseModel):
    request_id: str = Field(description="Unique identifier for the async request")
