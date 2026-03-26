from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import field_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.validators import ensure_non_empty_text


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EMPTY_SUBMISSION = "EMPTY_SUBMISSION"
    INVALID_SOURCE_TYPE = "INVALID_SOURCE_TYPE"
    UNSUPPORTED_UPLOAD_FORMAT = "UNSUPPORTED_UPLOAD_FORMAT"
    UPLOAD_TOO_LARGE = "UPLOAD_TOO_LARGE"
    UPLOAD_PARSE_FAILED = "UPLOAD_PARSE_FAILED"
    JOINT_INPUT_UNRATEABLE = "JOINT_INPUT_UNRATEABLE"
    INSUFFICIENT_CHAPTERS_INPUT = "INSUFFICIENT_CHAPTERS_INPUT"
    INSUFFICIENT_OUTLINE_INPUT = "INSUFFICIENT_OUTLINE_INPUT"
    JOINT_INPUT_MISMATCH = "JOINT_INPUT_MISMATCH"
    RESULT_BLOCKED = "RESULT_BLOCKED"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_STATE_CONFLICT = "TASK_STATE_CONFLICT"
    RESULT_NOT_FOUND = "RESULT_NOT_FOUND"
    RESULT_NOT_AVAILABLE = "RESULT_NOT_AVAILABLE"
    CONTRACT_INVALID = "CONTRACT_INVALID"
    RESULT_SCHEMA_INVALID = "RESULT_SCHEMA_INVALID"
    STAGE_SCHEMA_INVALID = "STAGE_SCHEMA_INVALID"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    TIMEOUT = "TIMEOUT"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


BLOCKED_ERROR_CODES = frozenset(
    {
        ErrorCode.JOINT_INPUT_UNRATEABLE,
        ErrorCode.INSUFFICIENT_CHAPTERS_INPUT,
        ErrorCode.INSUFFICIENT_OUTLINE_INPUT,
        ErrorCode.JOINT_INPUT_MISMATCH,
        ErrorCode.RESULT_BLOCKED,
    }
)

FAILED_ERROR_CODES = frozenset(
    {
        ErrorCode.CONTRACT_INVALID,
        ErrorCode.RESULT_SCHEMA_INVALID,
        ErrorCode.STAGE_SCHEMA_INVALID,
        ErrorCode.PROVIDER_FAILURE,
        ErrorCode.TIMEOUT,
        ErrorCode.DEPENDENCY_UNAVAILABLE,
        ErrorCode.INTERNAL_ERROR,
    }
)


class ErrorObject(SchemaModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None
    fieldErrors: dict[str, str] | None = None
    retryable: bool | None = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        return ensure_non_empty_text(value, "error.message")

    @field_validator("fieldErrors")
    @classmethod
    def validate_field_errors(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        return {
            ensure_non_empty_text(field_name, "fieldErrors.key"): ensure_non_empty_text(
                message,
                "fieldErrors.value",
            )
            for field_name, message in value.items()
        }
