from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from packages.schemas.output.envelope import ErrorEnvelope
from packages.schemas.output.error import ErrorCode, ErrorObject


class ApiError(Exception):
    def __init__(self, *, status_code: int, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(*, status_code: int, code: ErrorCode, message: str, field_errors: dict[str, str] | None = None) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorObject(
            code=code,
            message=message,
            fieldErrors=field_errors,
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump(mode="json"))


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return error_response(status_code=exc.status_code, code=exc.code, message=exc.message)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    field_errors: dict[str, str] = {}
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part != "body"]
        field_name = ".".join(location) if location else "body"
        field_errors[field_name] = error.get("msg", "输入参数不合法")
    return error_response(
        status_code=422,
        code=ErrorCode.VALIDATION_ERROR,
        message="输入参数不合法",
        field_errors=field_errors or None,
    )
