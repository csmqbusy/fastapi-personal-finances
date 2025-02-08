from fastapi import APIRouter
from .routes import (
    authentication_router,
    operations_router,
)

router_v1 = APIRouter()
router_v1.include_router(
    authentication_router,
    tags=["authentication"],
)
router_v1.include_router(
    operations_router,
    tags=["operations"],
)
