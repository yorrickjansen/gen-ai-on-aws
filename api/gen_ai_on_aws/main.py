import logging
import os

from fastapi import FastAPI
from mangum import Mangum

from gen_ai_on_aws.config import settings
from gen_ai_on_aws.routers import router

# Get logging level from environment variable or default to INFO
log_level_name = os.environ.get("LOGGING_LEVEL", "INFO")
log_level = getattr(logging, log_level_name.upper(), logging.INFO)

logger = logging.getLogger()
logger.setLevel(log_level)

# Set specific level for litellm to reduce noise
logging.getLogger("litellm").setLevel(logging.WARNING)


app = FastAPI(
    title="Gen AI on AWS",
    description="Generative AI on AWS",
    debug=settings.fastapi_debug,
    contact={
        "name": "Yorrick Jansen",
        "email": "yorrick@yorrickjansen.com",
    },
)

handler = Mangum(app, lifespan="off", api_gateway_base_path="/stage")

app.include_router(router)
