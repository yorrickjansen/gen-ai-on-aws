from fastapi import APIRouter

from gen_ai_on_aws.endpoints import endpoints

router = APIRouter()
router.include_router(endpoints.router, prefix="/endpoints", tags=["Endpoints"])
