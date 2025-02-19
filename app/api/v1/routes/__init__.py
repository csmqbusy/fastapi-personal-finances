from .auth_routes import router as authentication_router
from .spendings_routes import router as spendings_router


__all__ = [
    "authentication_router",
    "spendings_router",
]
