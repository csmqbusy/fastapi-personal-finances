from fastapi import APIRouter

from .auth import router as pages_auth


pages_router = APIRouter(tags=["Frontend"])
pages_router.include_router(pages_auth)

