import json
import logging
import os

import boto3
import litellm
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Setup module logger based on environment configuration
logger = logging.getLogger(__name__)


try:
    from worker.version import VERSION
except ImportError:
    VERSION = "local"


class LangFuseConfig(BaseModel):
    public_key: str = Field(description="The public key for LangFuse.")
    secret_key: str = Field(description="The secret key for LangFuse.")
    host: str = Field(description="The host for LangFuse.")


class Settings(BaseSettings):
    """Settings for the worker."""

    model: str = "anthropic/claude-sonnet-4-5-20250929"
    stack_name: str = "dev"  # Default to dev for testing
    logging_level: str = "INFO"
    anthropic_api_key_secret_name: str | None = None
    langfuse_public_key_secret_name: str | None = None
    langfuse_secret_key_secret_name: str | None = None
    langfuse_host: str = "https://us.cloud.langfuse.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()


session = boto3.session.Session()
client = session.client(service_name="secretsmanager")


def get_anthropic_api_key(stack_name: str) -> str:
    logger.info(f"Fetching API key for stack: {stack_name}")
    secret_name = (
        settings.anthropic_api_key_secret_name or f"gen-ai-on-aws/{stack_name}/anthropic_api_key"
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.error(f"Error fetching secret: {e}")
        raise

    return json.loads(get_secret_value_response["SecretString"])["key"]


def get_langfuse_config(stack_name: str) -> LangFuseConfig | None:
    public_key_secret = (
        settings.langfuse_public_key_secret_name
        or f"gen-ai-on-aws/{stack_name}/langfuse_public_key"
    )
    secret_key_secret = (
        settings.langfuse_secret_key_secret_name
        or f"gen-ai-on-aws/{stack_name}/langfuse_secret_key"
    )
    host = settings.langfuse_host

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager")

    try:
        public_key_response = client.get_secret_value(SecretId=public_key_secret)
        secret_key_response = client.get_secret_value(SecretId=secret_key_secret)

        return LangFuseConfig(
            public_key=json.loads(public_key_response["SecretString"])["key"],
            secret_key=json.loads(secret_key_response["SecretString"])["key"],
            host=host,
        )
    except Exception as e:
        logger.error(f"Error fetching Langfuse secrets: {e}")
        return None


if anthropic_api_key := get_anthropic_api_key(stack_name=settings.stack_name):
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key


# configure langfuse is running inside AWS Lambda
if os.environ.get("AWS_EXECUTION_ENV") is not None:
    if langfuse_config := get_langfuse_config(stack_name=settings.stack_name):
        os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_config.public_key
        os.environ["LANGFUSE_SECRET_KEY"] = langfuse_config.secret_key
        os.environ["LANGFUSE_HOST"] = langfuse_config.host

        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
