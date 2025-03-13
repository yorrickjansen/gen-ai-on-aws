import logging

from fastapi import FastAPI
from gen_ai_on_aws.config import settings
from gen_ai_on_aws.routers import router
from mangum import Mangum

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# TODO somehow this doesn't work
# logging.getLogger("litellm").setLevel(logging.WARNING)


app = FastAPI(
    title="Gen AI on AWS",
    description="Generative AI on AWS",
    debug=settings.fastapi_debug,
    contact={
        "name": "Yorrick Jansen",
        "email": "info@yorrickjansen.com",
    },
)

handler = Mangum(app, lifespan="off", api_gateway_base_path="/stage")

app.include_router(router)
