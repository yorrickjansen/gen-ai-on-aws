import logging
from typing import Optional

from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel, Field
from litellm import completion
import instructor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = FastAPI()
handler = Mangum(app)

# Create instructor client using litellm
client = instructor.from_litellm(completion)


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

    response = client.chat.completions.create(
        model="bedrock/us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Updated model name for litellm format
        messages=[
            {
                "role": "user",
                "content": text,
            }
        ],
        response_model=User,
    )
    return response
