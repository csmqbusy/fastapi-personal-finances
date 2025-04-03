from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import router_v1
from app.core.config import settings
from app.db import close_db
from app.pages import pages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()


main_app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)
main_app.mount(
    "/static", StaticFiles(directory=settings.pages.static_path), name="static"
)
main_app.include_router(
    router_v1,
    prefix=settings.api.prefix_v1,
)
main_app.include_router(
    pages_router,
    prefix=settings.pages.pages_prefix,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
