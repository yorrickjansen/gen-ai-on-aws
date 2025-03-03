import logging
from typing import Any, Dict, Optional

from anthropic import AnthropicBedrock
import instructor
from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel, Field

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI()
handler = Mangum(app)


# Patching the Anthropics client with the instructor for enhanced capabilities
client = instructor.from_anthropic(AnthropicBedrock())


class User(BaseModel):
    name: str = Field(description="The name of the user.")
    age: int = Field(description="The age of the user.")
    email: Optional[str] = Field(description="The email of the user.", default=None)


@app.get("/hello")
async def root() -> str:
    return "Hello, world!"


@app.post("/extract-user")
async def extract_user(text: str) -> User:
    # text = "My name is John Doe, I am 30 years old, and I don't have an email address."

    user_response = client.chat.completions.create(
        model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=1024,
        max_retries=0,
        messages=[
            {
                "role": "user",
                "content": text,
            }
        ],
        response_model=User,
    )
    return user_response
