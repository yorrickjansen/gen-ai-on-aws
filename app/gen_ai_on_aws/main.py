import logging
import os
from typing import Optional

import instructor
from fastapi import FastAPI
from litellm import completion
from mangum import Mangum
from pydantic import BaseModel, Field
import litellm

os.environ["LITELLM_LOG"] = "DEBUG"
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
litellm._turn_on_debug()


MODEL = os.environ["MODEL"]


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
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": text,
            }
        ],
        response_model=User,
    )
    return response
