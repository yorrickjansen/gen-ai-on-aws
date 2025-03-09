import logging
import os
import litellm
from fastapi import FastAPI
from gen_ai_on_aws.config import (
    get_anthropic_api_key,
    get_langfuse_config,
    FASTAPI_DEBUG,
)
from mangum import Mangum
from gen_ai_on_aws.routers import router


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# TODO somehow this doesn't work
# logging.getLogger("litellm").setLevel(logging.WARNING)


app = FastAPI(
    title="Gen AI on AWS",
    description="Generative AI on AWS",
    debug=FASTAPI_DEBUG,
    contact={
        "name": "Yorrick Jansen",
        "email": "info@yorrickjansen.com",
    },
)
handler = Mangum(app)

app.include_router(router)
