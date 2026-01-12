"""Authentication utilities for API endpoints."""

import os

from fastapi import Header, HTTPException, status
from loguru import logger


async def verify_webhook_auth(auth: str | None = Header(None)) -> str:
    """Verify webhook authentication header.

    This is a reusable dependency that can be used with any webhook endpoint
    that needs header-based authentication.

    Args:
        auth: The auth header value from the request

    Returns:
        The authenticated header value

    Raises:
        HTTPException: 401 Unauthorized if auth fails
    """
    expected_auth = os.environ.get("ELEVENLABS_WEBHOOK_AUTH")

    if not expected_auth:
        logger.error("ELEVENLABS_WEBHOOK_AUTH not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook authentication not configured",
        )

    if not auth:
        logger.warning("Missing auth header in webhook request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication header"
        )

    if auth != expected_auth:
        logger.warning(f"Invalid auth header received: {auth[:10]}..." if len(auth) > 10 else auth)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    return auth


def create_auth_dependency(env_var_name: str, header_name: str = "auth"):
    """Factory function to create custom auth dependencies.

    This allows creating auth dependencies for different services
    with different environment variables and header names.

    Args:
        env_var_name: Name of the environment variable containing the expected token
        header_name: Name of the header to check (default: "auth")

    Returns:
        A FastAPI dependency function for authentication

    Example:
        ```python
        # Create a custom auth dependency for another service
        verify_custom_auth = create_auth_dependency("CUSTOM_SERVICE_AUTH", "x-api-key")

        @router.post("/custom-webhook")
        async def custom_webhook(
            payload: dict,
            auth: str = Depends(verify_custom_auth)
        ):
            ...
        ```
    """

    async def verify_auth(header_value: str | None = Header(None, alias=header_name)) -> str:
        expected_auth = os.environ.get(env_var_name)

        if not expected_auth:
            logger.error(f"{env_var_name} not configured in environment")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured",
            )

        if not header_value:
            logger.warning(f"Missing {header_name} header in request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication header"
            )

        if header_value != expected_auth:
            logger.warning(f"Invalid {header_name} header received")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

        return header_value

    return verify_auth
