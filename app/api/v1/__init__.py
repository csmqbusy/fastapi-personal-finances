from fastapi import APIRouter
from .routes import (
    authentication_router,
    spendings_router,
)

router_v1 = APIRouter()
router_v1.include_router(
    authentication_router,
    tags=["Authentication"],
)
router_v1.include_router(
    spendings_router,
    tags=["Spendings"],
)
