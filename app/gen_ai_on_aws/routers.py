from fastapi import APIRouter
from gen_ai_on_aws.examples import examples


router = APIRouter()
router.include_router(examples.router, tags=["Examples"])
