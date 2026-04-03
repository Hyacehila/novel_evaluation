from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.scoring_pipeline.exceptions import PipelineFailureError
from packages.application.scoring_pipeline.models import StagePromptBinding
from packages.schemas.common.enums import EvaluationMode, InputComposition, StageName
from packages.schemas.output.error import ErrorCode
from packages.runtime.logging import log_event


_FAILURE_TYPE_TO_ERROR_CODE = {
    "provider_failure": ErrorCode.PROVIDER_FAILURE,
    "timeout": ErrorCode.TIMEOUT,
    "dependency_unavailable": ErrorCode.DEPENDENCY_UNAVAILABLE,
    "contract_invalid": ErrorCode.CONTRACT_INVALID,
}

_SANITIZED_FAILURE_MESSAGE_BY_ERROR_CODE = {
    ErrorCode.PROVIDER_FAILURE: "模型服务调用失败，请稍后重试。",
    ErrorCode.TIMEOUT: "模型服务响应超时，请稍后重试。",
    ErrorCode.DEPENDENCY_UNAVAILABLE: "模型依赖当前不可用，请稍后重试。",
    ErrorCode.CONTRACT_INVALID: "模型返回内容不满足约定格式。",
}

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProviderMessagePayload:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ProviderExecutionRequestPayload:
    taskId: str
    stage: StageName
    promptId: str
    promptVersion: str
    schemaVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    requestId: str
    messages: list[ProviderMessagePayload]
    inputComposition: InputComposition
    evaluationMode: EvaluationMode
    timeoutMs: int | None = None
    maxTokens: int | None = None
    responseFormat: str | dict[str, str] | None = None


def execute_provider_stage(
    *,
    provider_adapter: ProviderExecutionPort,
    binding: StagePromptBinding,
    task_id: str,
    stage: StageName,
    input_composition: InputComposition,
    evaluation_mode: EvaluationMode,
    user_payload: Mapping[str, Any],
    timeout_ms: int | None = None,
    max_tokens: int | None = None,
    response_format: str | dict[str, str] | None = None,
) -> Any:
    request_id = binding.request_id
    started_at = perf_counter()
    provider_request = ProviderExecutionRequestPayload(
        taskId=task_id,
        stage=stage,
        promptId=binding.prompt_id,
        promptVersion=binding.prompt_version,
        schemaVersion=binding.schema_version,
        rubricVersion=binding.rubric_version,
        providerId=binding.provider_id,
        modelId=binding.model_id,
        requestId=request_id,
        messages=[
            ProviderMessagePayload(role="system", content=binding.prompt_body),
            ProviderMessagePayload(role="user", content=json.dumps(dict(user_payload), ensure_ascii=False)),
        ],
        inputComposition=input_composition,
        evaluationMode=evaluation_mode,
        timeoutMs=timeout_ms,
        maxTokens=max_tokens,
        responseFormat=response_format,
    )
    log_event(
        logger,
        logging.INFO,
        "stage_provider_start",
        taskId=task_id,
        stage=stage,
        requestId=request_id,
        promptId=binding.prompt_id,
        promptVersion=binding.prompt_version,
        schemaVersion=binding.schema_version,
        rubricVersion=binding.rubric_version,
        providerId=binding.provider_id,
        modelId=binding.model_id,
    )
    try:
        result = provider_adapter.execute(provider_request)
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((perf_counter() - started_at) * 1000)
        error_code = _resolve_exception_error_code(exc)
        log_event(
            logger,
            logging.ERROR,
            "stage_provider_failed",
            taskId=task_id,
            stage=stage,
            requestId=request_id,
            promptVersion=binding.prompt_version,
            schemaVersion=binding.schema_version,
            rubricVersion=binding.rubric_version,
            providerId=binding.provider_id,
            modelId=binding.model_id,
            errorCode=error_code,
            durationMs=duration_ms,
        )
        raise PipelineFailureError(
            error_code=error_code,
            message=_sanitize_provider_failure_message(error_code=error_code),
        ) from exc
    duration_ms = int((perf_counter() - started_at) * 1000)
    failure_type = getattr(result, "failureType", None)
    if failure_type is not None:
        error_code = _resolve_failure_error_code(failure_type=failure_type)
        log_event(
            logger,
            logging.ERROR,
            "stage_provider_failed",
            taskId=task_id,
            stage=stage,
            requestId=request_id,
            promptVersion=binding.prompt_version,
            schemaVersion=binding.schema_version,
            rubricVersion=binding.rubric_version,
            providerId=binding.provider_id,
            modelId=binding.model_id,
            errorCode=error_code,
            durationMs=duration_ms,
        )
        raise PipelineFailureError(
            error_code=error_code,
            message=_sanitize_provider_failure_message(error_code=error_code),
        )
    raw_json = getattr(result, "rawJson", None)
    if not hasattr(result, "rawJson"):
        log_event(
            logger,
            logging.ERROR,
            "stage_provider_failed",
            taskId=task_id,
            stage=stage,
            requestId=request_id,
            promptVersion=binding.prompt_version,
            schemaVersion=binding.schema_version,
            rubricVersion=binding.rubric_version,
            providerId=binding.provider_id,
            modelId=binding.model_id,
            errorCode=ErrorCode.CONTRACT_INVALID,
            durationMs=duration_ms,
        )
        raise PipelineFailureError(
            error_code=ErrorCode.CONTRACT_INVALID,
            message=_sanitize_provider_failure_message(error_code=ErrorCode.CONTRACT_INVALID),
        )
    log_event(
        logger,
        logging.INFO,
        "stage_provider_completed",
        taskId=task_id,
        stage=stage,
        requestId=request_id,
        promptVersion=binding.prompt_version,
        schemaVersion=binding.schema_version,
        rubricVersion=binding.rubric_version,
        providerId=binding.provider_id,
        modelId=binding.model_id,
        durationMs=duration_ms,
    )
    return _thaw_json_like(raw_json)


def _resolve_failure_error_code(*, failure_type: Any) -> ErrorCode:
    normalized_failure_type = getattr(failure_type, "value", failure_type)
    if not isinstance(normalized_failure_type, str):
        return ErrorCode.PROVIDER_FAILURE
    return _FAILURE_TYPE_TO_ERROR_CODE.get(normalized_failure_type, ErrorCode.PROVIDER_FAILURE)



def _resolve_exception_error_code(exc: Exception) -> ErrorCode:
    failure_type = getattr(exc, "failure_type", None)
    if failure_type is not None:
        return _resolve_failure_error_code(failure_type=failure_type)
    exception_name = type(exc).__name__
    if "Timeout" in exception_name:
        return ErrorCode.TIMEOUT
    if "Connection" in exception_name:
        return ErrorCode.DEPENDENCY_UNAVAILABLE
    if "Contract" in exception_name:
        return ErrorCode.CONTRACT_INVALID
    return ErrorCode.PROVIDER_FAILURE



def _sanitize_provider_failure_message(*, error_code: ErrorCode) -> str:
    return _SANITIZED_FAILURE_MESSAGE_BY_ERROR_CODE.get(error_code, _SANITIZED_FAILURE_MESSAGE_BY_ERROR_CODE[ErrorCode.PROVIDER_FAILURE])



def _thaw_json_like(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json_like(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_like(item) for item in value]
    return value
