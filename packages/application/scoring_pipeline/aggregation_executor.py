from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.scoring_pipeline.exceptions import PipelineFailureError
from packages.application.scoring_pipeline.models import AggregationExecutionContext
from packages.application.scoring_pipeline.provider_support import execute_provider_stage
from packages.application.support.process_logging import log_event
from packages.schemas.common.enums import FatalRisk, StageName
from packages.schemas.output.error import ErrorCode
from packages.schemas.stages.aggregation import AggregatedRubricResult

logger = logging.getLogger(__name__)

_STAGE_TIMEOUT_MS = 90_000
_STAGE_MAX_TOKENS = 4_000
_SCHEMA_VALIDATION_MAX_ATTEMPTS = 2
def execute_aggregation(
    *,
    provider_adapter: ProviderExecutionPort,
    context: AggregationExecutionContext,
) -> AggregatedRubricResult:
    user_payload = {
        "taskId": context.task_id,
        "title": context.submission.title,
        "chapters": [chapter.content for chapter in context.submission.chapters or []],
        "outline": context.submission.outline.content if context.submission.outline is not None else None,
        "screening": context.screening.model_dump(mode="json"),
        "typeClassification": context.type_classification.model_dump(mode="json"),
        "rubric": context.rubric.model_dump(mode="json"),
        "typeLens": context.type_lens.model_dump(mode="json"),
        "consistency": context.consistency.model_dump(mode="json"),
    }
    for attempt in range(1, _SCHEMA_VALIDATION_MAX_ATTEMPTS + 1):
        payload = execute_provider_stage(
            provider_adapter=provider_adapter,
            binding=context.binding,
            task_id=context.task_id,
            stage=StageName.AGGREGATION,
            input_composition=context.screening.inputComposition,
            evaluation_mode=context.screening.evaluationMode,
            timeout_ms=_STAGE_TIMEOUT_MS,
            max_tokens=_STAGE_MAX_TOKENS,
            response_format={"type": "json_object"},
            user_payload=user_payload,
        )
        payload = _normalize_aggregation_payload(payload=payload, context=context)
        try:
            return AggregatedRubricResult.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            if attempt < _SCHEMA_VALIDATION_MAX_ATTEMPTS:
                log_event(
                    logger,
                    logging.WARNING,
                    "stage_schema_invalid_retry",
                    taskId=context.task_id,
                    stage=StageName.AGGREGATION,
                    promptVersion=context.binding.prompt_version,
                    schemaVersion=context.binding.schema_version,
                    rubricVersion=context.binding.rubric_version,
                    providerId=context.binding.provider_id,
                    modelId=context.binding.model_id,
                    errorCode=ErrorCode.STAGE_SCHEMA_INVALID,
                    attempt=attempt,
                    maxAttempts=_SCHEMA_VALIDATION_MAX_ATTEMPTS,
                )
                continue
            log_event(
                logger,
                logging.ERROR,
                "stage_schema_invalid",
                taskId=context.task_id,
                stage=StageName.AGGREGATION,
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
                message="aggregation 阶段输出不满足正式 schema。",
            ) from exc


def _normalize_aggregation_payload(*, payload: Any, context: AggregationExecutionContext) -> Any:
    if not isinstance(payload, Mapping):
        return payload
    normalized_payload: dict[str, Any] = dict(payload)
    overall_verdict = (
        _normalize_text_value(normalized_payload.get("overallVerdictDraft"))
        or _normalize_text_value(normalized_payload.get("editorVerdictDraft"))
    )
    overall_summary = (
        _normalize_text_value(normalized_payload.get("overallSummaryDraft"))
        or _normalize_text_value(normalized_payload.get("detailedAnalysisDraft"))
    )
    market_fit = _normalize_text_value(normalized_payload.get("marketFitDraft"))
    if overall_verdict is None or overall_summary is None or market_fit is None:
        return payload
    normalized_payload = {
        "taskId": context.task_id,
        "stage": StageName.AGGREGATION.value,
        "schemaVersion": context.binding.schema_version,
        "promptVersion": context.binding.prompt_version,
        "rubricVersion": context.binding.rubric_version,
        "providerId": context.binding.provider_id,
        "modelId": context.binding.model_id,
        "overallVerdictDraft": overall_verdict,
        "verdictSubQuote": _normalize_text_value(normalized_payload.get("verdictSubQuote")),
        "overallSummaryDraft": overall_summary,
        "platformCandidates": _normalize_platform_candidates(normalized_payload.get("platformCandidates")),
        "marketFitDraft": market_fit,
        "strengthCandidates": _normalize_text_list(normalized_payload.get("strengthCandidates")),
        "weaknessCandidates": _normalize_text_list(normalized_payload.get("weaknessCandidates")),
        "riskTags": _normalize_risk_tags(normalized_payload.get("riskTags")),
        "overallConfidence": _normalize_confidence(
            normalized_payload.get("overallConfidence"),
            fallback=context.consistency.confidence,
        ),
    }
    return normalized_payload


def _normalize_platform_candidates(raw_values: Any) -> list[dict[str, Any]]:
    """将 LLM 输出的 platformCandidates 规范化为 PlatformCandidate dict 列表。

    每个有效 item 必须是包含 name（非空字符串）、weight（整数）、pitchQuote（非空字符串）的 dict。
    格式不符的 item 直接丢弃，不做字符串降级。
    """
    if not isinstance(raw_values, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in raw_values:
        if not isinstance(item, Mapping):
            continue
        name = _normalize_text_value(item.get("name"))
        pitch_quote = _normalize_text_value(item.get("pitchQuote"))
        if not name or not pitch_quote:
            continue
        raw_weight = item.get("weight")
        if isinstance(raw_weight, float):
            raw_weight = int(raw_weight)
        weight = raw_weight if isinstance(raw_weight, int) and 0 <= raw_weight <= 100 else 0
        normalized.append({"name": name, "weight": weight, "pitchQuote": pitch_quote})
    return normalized


def _normalize_text_list(raw_values: Any) -> list[str]:
    if not isinstance(raw_values, list):
        return []
    normalized_values: list[str] = []
    for value in raw_values:
        text_value = _normalize_text_value(value)
        if text_value is not None:
            normalized_values.append(text_value)
    return normalized_values


def _normalize_text_value(raw_value: Any) -> str | None:
    if isinstance(raw_value, Mapping):
        for key in ("summary", "plot", "character", "pacing", "worldBuilding"):
            nested = raw_value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
        return None
    if not isinstance(raw_value, str):
        return None
    stripped = raw_value.strip()
    return stripped or None


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


def _normalize_confidence(raw_value: Any, *, fallback: float) -> float:
    if isinstance(raw_value, int | float):
        value = float(raw_value)
        if 0 <= value <= 1:
            return value
    return fallback
