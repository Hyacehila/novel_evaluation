from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from .errors import ApiError, api_error_handler, validation_error_handler
from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Novel Evaluation API", version="0.1.0")
    app.include_router(router)
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    return app


app = create_app()
