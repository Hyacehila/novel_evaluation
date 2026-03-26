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
from packages.application.support.process_logging import log_event
from packages.schemas.common.enums import EvaluationMode, InputComposition, StageName
from packages.schemas.output.error import ErrorCode


_FAILURE_TYPE_TO_ERROR_CODE = {
    "provider_failure": ErrorCode.PROVIDER_FAILURE,
    "timeout": ErrorCode.TIMEOUT,
    "dependency_unavailable": ErrorCode.DEPENDENCY_UNAVAILABLE,
    "contract_invalid": ErrorCode.CONTRACT_INVALID,
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
    result = provider_adapter.execute(provider_request)
    duration_ms = int((perf_counter() - started_at) * 1000)
    failure_type = getattr(result, "failureType", None)
    if failure_type is not None:
        error_code = _FAILURE_TYPE_TO_ERROR_CODE[getattr(failure_type, "value", failure_type)]
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
            message=result.message,
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
    return _thaw_json_like(result.rawJson)


def _thaw_json_like(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json_like(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_like(item) for item in value]
    return value
