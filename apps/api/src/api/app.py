from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from .dependencies import recover_processing_tasks
from .errors import ApiError, api_error_handler, validation_error_handler
from .routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    recover_processing_tasks()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Novel Evaluation API", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    return app


app = create_app()
