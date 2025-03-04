import logging
import os
from typing import Optional

import boto3
import instructor
import litellm
from fastapi import FastAPI
from litellm import completion
from mangum import Mangum
from pydantic import BaseModel, Field

os.environ["LITELLM_LOG"] = "DEBUG"
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
litellm._turn_on_debug()


MODEL = os.getenv("MODEL", "anthropic/claude-3-5-sonnet-20241022")


def get_anthropic_api_key():
    if not MODEL.startswith("anthropic/"):
        return None

    secret_name = os.getenv("ANTHROPIC_API_KEY_SECRET_NAME", "anthropic-api-key")
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.error(f"Error fetching secret: {e}")
        raise

    return get_secret_value_response["SecretString"]


if anthropic_api_key := get_anthropic_api_key():
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key


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


# app/gen_ai_on_aws/__init__.py
