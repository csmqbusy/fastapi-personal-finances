from .auth_routes import router as authentication_router
from .spendings_routes import router as spendings_router
from .income_routes import router as income_router


__all__ = [
    "authentication_router",
    "spendings_router",
    "income_router",
]
