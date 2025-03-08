import json
import logging
import os

import boto3
from gen_ai_on_aws.types import LangFuseConfig

logger = logging.getLogger()

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
