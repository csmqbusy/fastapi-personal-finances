from fastapi import APIRouter

from .auth import router as pages_auth
from .income import router as pages_income
from .saving_goals import router as pages_saving_goals
from .spendings import router as pages_spendings

pages_router = APIRouter(tags=["Frontend"])
pages_router.include_router(pages_auth)
pages_router.include_router(pages_spendings)
pages_router.include_router(pages_income)
pages_router.include_router(pages_saving_goals)
