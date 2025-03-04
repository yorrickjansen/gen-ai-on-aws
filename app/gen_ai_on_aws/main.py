import logging
import os
from typing import Optional

import boto3
import instructor
from fastapi import FastAPI
from litellm import completion
from mangum import Mangum
from pydantic import BaseModel, Field

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# TODO somehow this doesn't work
# logging.getLogger("litellm").setLevel(logging.WARNING)


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


class ExtractUserRequest(BaseModel):
    text: str = Field(description="The text to extract user information from.")


@app.get("/hello")
async def root() -> str:
    return "Hello, world!"


@app.post("/extract-user")
async def extract_user(request: ExtractUserRequest) -> User | None:
    logger.info(f"Extracting user from text: {request.text}")

    response = client.chat.completions.create(
        model=MODEL,
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
    )
    return response


# app/gen_ai_on_aws/__init__.py
