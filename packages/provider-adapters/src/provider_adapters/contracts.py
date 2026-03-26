from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from pydantic import Field, field_serializer, field_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import EvaluationMode, InputComposition, StageName
from packages.schemas.common.validators import ensure_non_empty_text, ensure_optional_text
from packages.schemas.output.error import ErrorCode

ProviderStructuredScalar = str | int | float | bool | None
ProviderStructuredOutput = Mapping[str, Any] | tuple[Any, ...] | ProviderStructuredScalar


class ProviderFailureType(StrEnum):
    PROVIDER_FAILURE = "provider_failure"
    TIMEOUT = "timeout"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    CONTRACT_INVALID = "contract_invalid"


FAILURE_TYPE_TO_ERROR_CODE = MappingProxyType(
    {
        ProviderFailureType.PROVIDER_FAILURE: ErrorCode.PROVIDER_FAILURE,
        ProviderFailureType.TIMEOUT: ErrorCode.TIMEOUT,
        ProviderFailureType.DEPENDENCY_UNAVAILABLE: ErrorCode.DEPENDENCY_UNAVAILABLE,
        ProviderFailureType.CONTRACT_INVALID: ErrorCode.CONTRACT_INVALID,
    }
)

DEFAULT_RETRYABLE_BY_FAILURE_TYPE = MappingProxyType(
    {
        ProviderFailureType.PROVIDER_FAILURE: True,
        ProviderFailureType.TIMEOUT: True,
        ProviderFailureType.DEPENDENCY_UNAVAILABLE: True,
        ProviderFailureType.CONTRACT_INVALID: False,
    }
)


class ProviderMessage(SchemaModel):
    role: str
    content: str

    @field_validator("role", "content")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "provider message field")


def _freeze_structured_output(value: Any) -> ProviderStructuredOutput:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        frozen_items: dict[str, ProviderStructuredOutput] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("rawJson 仅允许字符串键。")
            frozen_items[key] = _freeze_structured_output(item)
        return MappingProxyType(frozen_items)
    if isinstance(value, list | tuple):
        return tuple(_freeze_structured_output(item) for item in value)
    raise ValueError("rawJson 仅允许 JSON 风格的结构化内容。")


def _serialize_structured_output(value: ProviderStructuredOutput) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _serialize_structured_output(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_serialize_structured_output(item) for item in value]
    return value


class ProviderExecutionRequest(SchemaModel):
    taskId: str
    stage: StageName
    promptId: str
    promptVersion: str
    schemaVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    requestId: str
    messages: list[ProviderMessage] = Field(min_length=1)
    inputComposition: InputComposition | None = None
    evaluationMode: EvaluationMode | None = None
    timeoutMs: int | None = Field(default=None, ge=1)
    responseFormat: str | dict[str, Any] | None = None

    @field_validator(
        "taskId",
        "promptId",
        "promptVersion",
        "schemaVersion",
        "rubricVersion",
        "providerId",
        "modelId",
        "requestId",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "provider request field")

    @field_validator("responseFormat")
    @classmethod
    def validate_response_format(cls, value: str | dict[str, Any] | None) -> str | dict[str, Any] | None:
        if value is None or isinstance(value, dict):
            return value
        return ensure_non_empty_text(value, "responseFormat")


class ProviderExecutionSuccess(SchemaModel):
    providerId: str
    modelId: str
    requestId: str
    providerRequestId: str | None = None
    durationMs: int = Field(ge=0)
    rawText: str
    rawJson: ProviderStructuredOutput = None

    @field_validator("rawJson", mode="after")
    @classmethod
    def freeze_raw_json(cls, value: ProviderStructuredOutput) -> ProviderStructuredOutput:
        return _freeze_structured_output(value)

    @field_serializer("rawJson")
    def serialize_raw_json(self, value: ProviderStructuredOutput) -> Any:
        return _serialize_structured_output(value)

    @field_validator("providerId", "modelId", "requestId", "rawText")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "provider success field")

    @field_validator("providerRequestId")
    @classmethod
    def validate_provider_request_id(cls, value: str | None) -> str | None:
        return ensure_optional_text(value, "providerRequestId")


class ProviderExecutionFailure(SchemaModel):
    providerId: str
    modelId: str
    requestId: str
    providerRequestId: str | None = None
    durationMs: int = Field(ge=0)
    failureType: ProviderFailureType
    message: str
    retryable: bool

    @field_validator("providerId", "modelId", "requestId", "message")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "provider failure field")

    @field_validator("providerRequestId")
    @classmethod
    def validate_provider_request_id(cls, value: str | None) -> str | None:
        return ensure_optional_text(value, "providerRequestId")


ProviderExecutionResult = ProviderExecutionSuccess | ProviderExecutionFailure


def map_failure_type_to_error_code(failure_type: ProviderFailureType) -> ErrorCode:
    return FAILURE_TYPE_TO_ERROR_CODE[failure_type]


def default_retryable_for_failure_type(failure_type: ProviderFailureType) -> bool:
    return DEFAULT_RETRYABLE_BY_FAILURE_TYPE[failure_type]


def build_provider_failure(
    *,
    provider_id: str,
    model_id: str,
    request_id: str,
    provider_request_id: str | None,
    duration_ms: int,
    failure_type: ProviderFailureType,
    message: str,
    retryable: bool | None = None,
) -> ProviderExecutionFailure:
    resolved_retryable = (
        default_retryable_for_failure_type(failure_type) if retryable is None else retryable
    )
    return ProviderExecutionFailure(
        providerId=provider_id,
        modelId=model_id,
        requestId=request_id,
        providerRequestId=provider_request_id,
        durationMs=duration_ms,
        failureType=failure_type,
        message=message,
        retryable=resolved_retryable,
    )
