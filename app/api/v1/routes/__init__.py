from .auth_routes import router as authentication_router
from .income_routes import router as income_router
from .saving_goals_routes import router as saving_goals_router
from .spendings_routes import router as spendings_router

__all__ = [
    "authentication_router",
    "spendings_router",
    "income_router",
    "saving_goals_router",
]
