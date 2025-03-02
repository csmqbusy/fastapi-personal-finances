from fastapi import APIRouter
from .routes import (
    authentication_router,
    spendings_router,
    income_router,
    saving_goals_router,
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
router_v1.include_router(
    income_router,
    tags=["Income"],
)
router_v1.include_router(
    saving_goals_router,
    tags=["Saving Goals"],
)
