import logging
import os
from typing import Optional

import instructor
import litellm
from fastapi import FastAPI
from gen_ai_on_aws.config import get_anthropic_api_key, get_langfuse_config
from gen_ai_on_aws.types import ExtractUserRequest, User
from litellm import completion
from mangum import Mangum

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# TODO somehow this doesn't work
# logging.getLogger("litellm").setLevel(logging.WARNING)


MODEL = os.getenv("MODEL", "anthropic/claude-3-5-sonnet-20241022")


if anthropic_api_key := get_anthropic_api_key(model=MODEL):
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key


if langfuse_config := get_langfuse_config():
    os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_config.public_key
    os.environ["LANGFUSE_SECRET_KEY"] = langfuse_config.secret_key
    os.environ["LANGFUSE_HOST"] = langfuse_config.host


litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]


app = FastAPI()
handler = Mangum(app)

# Create instructor client using litellm
client = instructor.from_litellm(completion)


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
