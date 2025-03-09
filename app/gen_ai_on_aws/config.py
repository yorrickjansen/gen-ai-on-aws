import os
import logging
import boto3
import json
import litellm
from gen_ai_on_aws.types import LangFuseConfig


logger = logging.getLogger(__name__)


try:
    from gen_ai_on_aws.version import VERSION
except ImportError:
    VERSION = "local"


MODEL = os.getenv("MODEL", "anthropic/claude-3-5-sonnet-20241022")
STACK_NAME = os.environ["STACK_NAME"]
FASTAPI_DEBUG = os.environ.get("FASTAPI_DEBUG", "false").lower() in ["1", "true", "yes"]


session = boto3.session.Session()
client = session.client(service_name="secretsmanager")


def get_anthropic_api_key(stack_name: str) -> str:
    logger.info(f"Fetching API key for stack: {stack_name}")
    secret_name = os.getenv(
        "ANTHROPIC_API_KEY_SECRET_NAME", f"gen-ai-on-aws/{stack_name}/anthropic_api_key"
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.error(f"Error fetching secret: {e}")
        raise

    return json.loads(get_secret_value_response["SecretString"])["key"]


def get_langfuse_config(stack_name: str) -> LangFuseConfig | None:
    public_key_secret = os.getenv(
        "LANGFUSE_PUBLIC_KEY_SECRET_NAME",
        f"gen-ai-on-aws/{stack_name}/langfuse_public_key",
    )
    secret_key_secret = os.getenv(
        "LANGFUSE_SECRET_KEY_SECRET_NAME",
        f"gen-ai-on-aws/{stack_name}/langfuse_secret_key",
    )
    host = os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")

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


if anthropic_api_key := get_anthropic_api_key(stack_name=STACK_NAME):
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key


# configure langfuse is running inside AWS Lambda
if os.environ.get("AWS_EXECUTION_ENV") is not None:
    if langfuse_config := get_langfuse_config(stack_name=STACK_NAME):
        os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_config.public_key
        os.environ["LANGFUSE_SECRET_KEY"] = langfuse_config.secret_key
        os.environ["LANGFUSE_HOST"] = langfuse_config.host

        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
