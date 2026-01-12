import json
import logging
import os

import boto3
import litellm
from pydantic_settings import BaseSettings, SettingsConfigDict

from gen_ai_on_aws.types import LangFuseConfig

# Setup module logger based on environment configuration
logger = logging.getLogger(__name__)


try:
    from gen_ai_on_aws.version import VERSION
except ImportError:
    VERSION = "local"


class Settings(BaseSettings):
    """Settings for the application."""

    model: str = "anthropic/claude-sonnet-4-5-20250929"
    stack_name: str = ""
    fastapi_debug: bool = False
    logging_level: str = "INFO"

    # Direct API keys (for local development via .env)
    anthropic_api_key: str | None = None
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://us.cloud.langfuse.com"

    # AWS Secrets Manager secret names (for AWS deployment)
    anthropic_api_key_secret_name: str | None = None
    langfuse_public_key_secret_name: str | None = None
    langfuse_secret_key_secret_name: str | None = None

    sqs_queue_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


settings = Settings()


def get_anthropic_api_key_from_secrets_manager(stack_name: str) -> str:
    """Fetch Anthropic API key from AWS Secrets Manager.

    Args:
        stack_name: The stack name used to construct the secret name

    Returns:
        The API key from Secrets Manager
    """
    logger.info(f"Fetching API key from Secrets Manager for stack: {stack_name}")
    secret_name = (
        settings.anthropic_api_key_secret_name or f"gen-ai-on-aws/{stack_name}/anthropic_api_key"
    )

    session = boto3.Session()
    client = session.client(service_name="secretsmanager")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.error(f"Error fetching secret {secret_name}: {e}")
        print(f"Error fetching secret {secret_name}: {e}")
        raise

    return json.loads(get_secret_value_response["SecretString"])["key"]


def get_langfuse_config_from_secrets_manager(stack_name: str) -> LangFuseConfig | None:
    """Fetch Langfuse configuration from AWS Secrets Manager.

    Args:
        stack_name: The stack name used to construct the secret names

    Returns:
        LangFuseConfig if successful, None otherwise
    """
    public_key_secret = (
        settings.langfuse_public_key_secret_name
        or f"gen-ai-on-aws/{stack_name}/langfuse_public_key"
    )
    secret_key_secret = (
        settings.langfuse_secret_key_secret_name
        or f"gen-ai-on-aws/{stack_name}/langfuse_secret_key"
    )
    host = settings.langfuse_host

    session = boto3.Session()
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


# Configure secrets based on environment
# When running in AWS Lambda (AWS_EXECUTION_ENV is set), load from Secrets Manager
# Otherwise, use direct values from .env file
if os.environ.get("AWS_EXECUTION_ENV") is not None:
    logger.info("Running in AWS Lambda - loading secrets from Secrets Manager")

    # Load Anthropic API key from Secrets Manager
    if anthropic_api_key := get_anthropic_api_key_from_secrets_manager(
        stack_name=settings.stack_name
    ):
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key

    # Load Langfuse config from Secrets Manager
    if langfuse_config := get_langfuse_config_from_secrets_manager(stack_name=settings.stack_name):
        os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_config.public_key
        os.environ["LANGFUSE_SECRET_KEY"] = langfuse_config.secret_key
        os.environ["LANGFUSE_HOST"] = langfuse_config.host

        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
else:
    logger.info("Running locally - using secrets from .env file")

    # Use direct values from settings (loaded from .env)
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

    if settings.langfuse_public_key and settings.langfuse_secret_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host

        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
