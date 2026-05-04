from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.scoring_pipeline.exceptions import PipelineFailureError
from packages.application.scoring_pipeline.models import ScreeningExecutionContext
from packages.application.scoring_pipeline.provider_support import execute_provider_stage
from packages.schemas.common.enums import EvaluationMode, FatalRisk, InputComposition, StageName, Sufficiency
from packages.schemas.input.screening import InputScreeningResult
from packages.schemas.output.error import ErrorCode
from packages.runtime.logging import log_event

logger = logging.getLogger(__name__)

_STAGE_TIMEOUT_MS = 90_000
_STAGE_MAX_TOKENS = 1_500


def execute_screening(
    *,
    provider_adapter: ProviderExecutionPort,
    context: ScreeningExecutionContext,
) -> InputScreeningResult:
    payload = execute_provider_stage(
        provider_adapter=provider_adapter,
        binding=context.binding,
        task_id=context.task_id,
        stage=StageName.INPUT_SCREENING,
        input_composition=InputComposition(context.input_composition),
        analysis_mode=context.analysis_mode,
        evaluation_mode=context.evaluation_mode_hint,
        timeout_ms=_STAGE_TIMEOUT_MS,
        max_tokens=_STAGE_MAX_TOKENS,
        response_format={"type": "json_object"},
        user_payload={
            "taskId": context.task_id,
            "title": context.submission.title,
            "inputComposition": context.input_composition,
            "analysisMode": context.analysis_mode.value,
            "evaluationModeHint": context.evaluation_mode_hint.value,
            "chapters": [chapter.content for chapter in context.submission.chapters or []],
            "outline": context.submission.outline.content if context.submission.outline is not None else None,
        },
    )
    payload = _normalize_screening_payload(payload=payload, context=context)
    try:
        return InputScreeningResult.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
        log_event(
            logger,
            logging.ERROR,
            "stage_schema_invalid",
            taskId=context.task_id,
            stage=StageName.INPUT_SCREENING,
            promptVersion=context.binding.prompt_version,
            schemaVersion=context.binding.schema_version,
            rubricVersion=context.binding.rubric_version,
            providerId=context.binding.provider_id,
            modelId=context.binding.model_id,
            errorCode=ErrorCode.STAGE_SCHEMA_INVALID,
            durationMs=0,
        )
        raise PipelineFailureError(
            error_code=ErrorCode.STAGE_SCHEMA_INVALID,
            message="input_screening 阶段输出不满足正式 schema。",
        ) from exc


def _normalize_screening_payload(*, payload: Any, context: ScreeningExecutionContext) -> Any:
    if not isinstance(payload, Mapping):
        return payload
    normalized_payload: dict[str, Any] = dict(payload)
    normalized_payload.update(
        {
            "taskId": context.task_id,
            "stage": StageName.INPUT_SCREENING.value,
            "schemaVersion": context.binding.schema_version,
            "promptVersion": context.binding.prompt_version,
            "rubricVersion": context.binding.rubric_version,
            "providerId": context.binding.provider_id,
            "modelId": context.binding.model_id,
            "inputComposition": context.submission.inputComposition.value,
            "analysisMode": context.submission.analysisMode.value,
            "hasChapters": context.submission.hasChapters,
            "hasOutline": context.submission.hasOutline,
            "riskTags": _normalize_risk_tags(normalized_payload.get("riskTags")),
            "rejectionReasons": _normalize_text_list(normalized_payload.get("rejectionReasons")),
            "confidence": _normalize_confidence(normalized_payload.get("confidence"), fallback=0.5),
        }
    )
    normalized_payload["chaptersSufficiency"] = _normalize_sufficiency(
        normalized_payload.get("chaptersSufficiency"),
        present=context.submission.hasChapters,
    )
    normalized_payload["outlineSufficiency"] = _normalize_sufficiency(
        normalized_payload.get("outlineSufficiency"),
        present=context.submission.hasOutline,
    )
    normalized_payload["evaluationMode"] = _resolve_evaluation_mode(normalized_payload)
    return normalized_payload


def _normalize_sufficiency(raw_value: Any, *, present: bool) -> str:
    allowed_values = {item.value for item in Sufficiency}
    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if stripped in allowed_values:
            return stripped
    return Sufficiency.SUFFICIENT.value if present else Sufficiency.MISSING.value


def _resolve_evaluation_mode(payload: Mapping[str, Any]) -> str:
    return EvaluationMode.FULL.value


def _normalize_risk_tags(raw_risk_tags: Any) -> list[str]:
    if not isinstance(raw_risk_tags, list):
        return []
    allowed_risk_tags = {risk.value for risk in FatalRisk}
    normalized_risk_tags: list[str] = []
    for value in raw_risk_tags:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if stripped in allowed_risk_tags and stripped not in normalized_risk_tags:
            normalized_risk_tags.append(stripped)
    return normalized_risk_tags


def _normalize_text_list(raw_values: Any) -> list[str]:
    if not isinstance(raw_values, list):
        return []
    normalized_values: list[str] = []
    for value in raw_values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if stripped:
            normalized_values.append(stripped)
    return normalized_values


def _normalize_confidence(raw_value: Any, *, fallback: float) -> float:
    if isinstance(raw_value, int | float):
        value = float(raw_value)
        if 0 <= value <= 1:
            return value
    return fallback
