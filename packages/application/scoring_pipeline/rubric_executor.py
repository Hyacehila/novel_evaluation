from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.scoring_pipeline.exceptions import PipelineFailureError
from packages.application.scoring_pipeline.models import RubricExecutionContext
from packages.application.scoring_pipeline.provider_support import execute_provider_stage
from packages.application.support.process_logging import log_event
from packages.schemas.common.enums import AxisId, FatalRisk, ScoreBand, SkeletonDimensionId, StageName
from packages.schemas.output.error import ErrorCode
from packages.schemas.stages.rubric import RubricEvaluationSet, RubricEvaluationSlice

logger = logging.getLogger(__name__)

_STAGE_TIMEOUT_MS = 90_000
_STAGE_MAX_TOKENS = 6_000
_SCHEMA_VALIDATION_MAX_ATTEMPTS = 2
RUBRIC_SLICE_PLAN: tuple[tuple[AxisId, ...], ...] = (
    (AxisId.HOOK_RETENTION, AxisId.SERIAL_MOMENTUM, AxisId.CHARACTER_DRIVE),
    (AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF, AxisId.SETTING_DIFFERENTIATION),
    (AxisId.PLATFORM_FIT, AxisId.COMMERCIAL_POTENTIAL),
)
_DEFAULT_SKELETON_DIMENSIONS_BY_AXIS = {
    AxisId.HOOK_RETENTION.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
    AxisId.SERIAL_MOMENTUM.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
    AxisId.CHARACTER_DRIVE.value: SkeletonDimensionId.CHARACTER_MOMENTUM.value,
    AxisId.NARRATIVE_CONTROL.value: SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    AxisId.PACING_PAYOFF.value: SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    AxisId.SETTING_DIFFERENTIATION.value: SkeletonDimensionId.NOVELTY_UTILITY.value,
    AxisId.PLATFORM_FIT.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
    AxisId.COMMERCIAL_POTENTIAL.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
}
_SKELETON_DIMENSION_ALIASES = {
    SkeletonDimensionId.MARKET_ATTRACTION.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
    "conflict": SkeletonDimensionId.MARKET_ATTRACTION.value,
    "stakes": SkeletonDimensionId.MARKET_ATTRACTION.value,
    "progression": SkeletonDimensionId.MARKET_ATTRACTION.value,
    "arcs": SkeletonDimensionId.MARKET_ATTRACTION.value,
    "genre_conventions": SkeletonDimensionId.MARKET_ATTRACTION.value,
    "audience_expectations": SkeletonDimensionId.MARKET_ATTRACTION.value,
    "longevity": SkeletonDimensionId.MARKET_ATTRACTION.value,
    "marketability": SkeletonDimensionId.MARKET_ATTRACTION.value,
    SkeletonDimensionId.NARRATIVE_EXECUTION.value: SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    "clarity": SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    "flow": SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    "pacing": SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    "satisfaction": SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    SkeletonDimensionId.CHARACTER_MOMENTUM.value: SkeletonDimensionId.CHARACTER_MOMENTUM.value,
    "protagonist": SkeletonDimensionId.CHARACTER_MOMENTUM.value,
    "motivation": SkeletonDimensionId.CHARACTER_MOMENTUM.value,
    "relationships": SkeletonDimensionId.CHARACTER_MOMENTUM.value,
    SkeletonDimensionId.NOVELTY_UTILITY.value: SkeletonDimensionId.NOVELTY_UTILITY.value,
    "originality": SkeletonDimensionId.NOVELTY_UTILITY.value,
    "hook": SkeletonDimensionId.NOVELTY_UTILITY.value,
    "novelty": SkeletonDimensionId.NOVELTY_UTILITY.value,
    "differentiation": SkeletonDimensionId.NOVELTY_UTILITY.value,
}
_SOURCE_SPAN_KEYS = {
    "chapters": "chapterRef",
    "outline": "outlineRef",
    "cross_input": "crossInputRef",
}
_SCORE_BAND_ALIASES = {
    ScoreBand.ZERO.value: ScoreBand.ZERO.value,
    ScoreBand.ONE.value: ScoreBand.ONE.value,
    ScoreBand.TWO.value: ScoreBand.TWO.value,
    ScoreBand.THREE.value: ScoreBand.THREE.value,
    ScoreBand.FOUR.value: ScoreBand.FOUR.value,
    "very_low": ScoreBand.ZERO.value,
    "low": ScoreBand.ONE.value,
    "medium_low": ScoreBand.ONE.value,
    "medium": ScoreBand.TWO.value,
    "medium_high": ScoreBand.THREE.value,
    "high": ScoreBand.FOUR.value,
    "very_high": ScoreBand.FOUR.value,
    "弱": ScoreBand.ONE.value,
    "中": ScoreBand.TWO.value,
    "高": ScoreBand.FOUR.value,
}


def execute_rubric(
    *,
    provider_adapter: ProviderExecutionPort,
    context: RubricExecutionContext,
) -> RubricEvaluationSet:
    slices = [
        execute_rubric_slice(
            provider_adapter=provider_adapter,
            context=RubricExecutionContext(
                task_id=context.task_id,
                submission=context.submission,
                screening=context.screening,
                binding=context.binding,
                requested_axes=requested_axes,
            ),
        )
        for requested_axes in RUBRIC_SLICE_PLAN
    ]
    return merge_rubric_slices(context=context, slices=slices)



def execute_rubric_slice(
    *,
    provider_adapter: ProviderExecutionPort,
    context: RubricExecutionContext,
) -> RubricEvaluationSlice:
    requested_axes = [axis_id.value for axis_id in context.requested_axes]
    user_payload = {
        "taskId": context.task_id,
        "title": context.submission.title,
        "inputComposition": context.screening.inputComposition.value,
        "evaluationMode": context.screening.evaluationMode.value,
        "requestedAxes": requested_axes,
        "chapters": [chapter.content for chapter in context.submission.chapters or []],
        "outline": context.submission.outline.content if context.submission.outline is not None else None,
        "screening": context.screening.model_dump(mode="json"),
    }
    for attempt in range(1, _SCHEMA_VALIDATION_MAX_ATTEMPTS + 1):
        payload = execute_provider_stage(
            provider_adapter=provider_adapter,
            binding=context.binding,
            task_id=context.task_id,
            stage=StageName.RUBRIC_EVALUATION,
            input_composition=context.screening.inputComposition,
            evaluation_mode=context.screening.evaluationMode,
            timeout_ms=_STAGE_TIMEOUT_MS,
            max_tokens=_STAGE_MAX_TOKENS,
            response_format={"type": "json_object"},
            user_payload=user_payload,
        )
        payload = _normalize_rubric_payload(payload=payload, context=context)
        try:
            return RubricEvaluationSlice.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            if attempt < _SCHEMA_VALIDATION_MAX_ATTEMPTS:
                log_event(
                    logger,
                    logging.WARNING,
                    "stage_schema_invalid_retry",
                    taskId=context.task_id,
                    stage=StageName.RUBRIC_EVALUATION,
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
                stage=StageName.RUBRIC_EVALUATION,
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
                message="rubric_evaluation 阶段输出不满足正式 schema。",
            ) from exc



def merge_rubric_slices(*, context: RubricExecutionContext, slices: list[RubricEvaluationSlice]) -> RubricEvaluationSet:
    items_by_axis = {
        item.axisId: item
        for rubric_slice in slices
        for item in rubric_slice.items
    }
    axis_summaries = {
        axis_id: summary
        for rubric_slice in slices
        for axis_id, summary in rubric_slice.axisSummaries.items()
    }
    risk_tags = list({risk_tag for rubric_slice in slices for risk_tag in rubric_slice.riskTags})
    missing_required_axes = [axis_id for axis_id in AxisId if axis_id not in items_by_axis]
    try:
        return RubricEvaluationSet(
            taskId=context.task_id,
            stage=StageName.RUBRIC_EVALUATION,
            schemaVersion=context.binding.schema_version,
            promptVersion=context.binding.prompt_version,
            rubricVersion=context.binding.rubric_version,
            providerId=context.binding.provider_id,
            modelId=context.binding.model_id,
            inputComposition=context.screening.inputComposition,
            evaluationMode=context.screening.evaluationMode,
            items=[items_by_axis[axis_id] for axis_id in AxisId],
            axisSummaries={axis_id: axis_summaries[axis_id] for axis_id in AxisId},
            missingRequiredAxes=missing_required_axes,
            riskTags=risk_tags,
            overallConfidence=min(rubric_slice.overallConfidence for rubric_slice in slices),
        )
    except Exception as exc:  # noqa: BLE001
        raise PipelineFailureError(
            error_code=ErrorCode.STAGE_SCHEMA_INVALID,
            message="rubric_evaluation 阶段输出不满足正式 schema。",
        ) from exc



def _normalize_rubric_payload(*, payload: Any, context: RubricExecutionContext) -> Any:
    if not isinstance(payload, Mapping):
        return payload
    normalized_payload: dict[str, Any] = dict(payload)
    requested_axis_values = {axis_id.value for axis_id in context.requested_axes}
    normalized_items = normalized_payload.get("items")
    if isinstance(normalized_items, list):
        normalized_items = [_normalize_rubric_item(item) for item in normalized_items]
        if requested_axis_values:
            normalized_items = [
                item
                for item in normalized_items
                if isinstance(item, Mapping) and item.get("axisId") in requested_axis_values
            ]
        normalized_payload["items"] = normalized_items
    normalized_axis_summaries = _normalize_axis_summaries(
        raw_axis_summaries=normalized_payload.get("axisSummaries"),
        normalized_items=normalized_items,
    )
    if requested_axis_values:
        normalized_axis_summaries = {
            axis_id: summary
            for axis_id, summary in normalized_axis_summaries.items()
            if axis_id in requested_axis_values
        }
    normalized_missing_required_axes = _normalize_axis_ids(normalized_payload.get("missingRequiredAxes"))
    if requested_axis_values:
        normalized_missing_required_axes = [
            axis_id for axis_id in normalized_missing_required_axes if axis_id in requested_axis_values
        ]
    normalized_payload.update(
        {
            "taskId": context.task_id,
            "stage": StageName.RUBRIC_EVALUATION.value,
            "schemaVersion": context.binding.schema_version,
            "promptVersion": context.binding.prompt_version,
            "rubricVersion": context.binding.rubric_version,
            "providerId": context.binding.provider_id,
            "modelId": context.binding.model_id,
            "inputComposition": context.screening.inputComposition.value,
            "evaluationMode": context.screening.evaluationMode.value,
            "requestedAxes": [axis_id.value for axis_id in context.requested_axes],
            "axisSummaries": normalized_axis_summaries,
            "missingRequiredAxes": normalized_missing_required_axes,
            "riskTags": _normalize_risk_tags(normalized_payload.get("riskTags")),
        }
    )
    return normalized_payload



def _normalize_rubric_item(item: Any) -> Any:
    if not isinstance(item, Mapping):
        return item
    normalized_item: dict[str, Any] = dict(item)
    axis_key = _normalize_axis_key(normalized_item.get("axisId"))
    item_confidence = _normalize_confidence(normalized_item.get("confidence"), fallback=0.5)
    normalized_item["confidence"] = item_confidence
    normalized_item["scoreBand"] = _normalize_score_band(normalized_item.get("scoreBand"))
    normalized_item["evidenceRefs"] = _normalize_evidence_refs(
        normalized_item.get("evidenceRefs"),
        item_confidence=item_confidence,
        fallback_excerpt=normalized_text_value(normalized_item.get("reason")) or "模型未提供明确证据摘录。",
    )
    normalized_item["riskTags"] = _normalize_risk_tags(normalized_item.get("riskTags"))
    normalized_item["blockingSignals"] = _normalize_text_list(normalized_item.get("blockingSignals"))
    normalized_item["affectedSkeletonDimensions"] = _normalize_skeleton_dimensions(
        normalized_item.get("affectedSkeletonDimensions"),
        axis_key=axis_key,
    )
    return normalized_item



def normalized_ref_source_type(reference: Any) -> str | None:
    if not isinstance(reference, Mapping):
        return None
    raw_source_type = reference.get("sourceType")
    if isinstance(raw_source_type, str):
        return raw_source_type.strip()
    return None



def _normalize_evidence_refs(
    raw_references: Any,
    *,
    item_confidence: float,
    fallback_excerpt: str,
) -> list[Any]:
    if not isinstance(raw_references, list) or not raw_references:
        return [
            _normalize_evidence_ref(
                None,
                source_type=None,
                item_confidence=item_confidence,
                fallback_excerpt=fallback_excerpt,
            )
        ]
    normalized_references: list[Any] = []
    for reference in raw_references:
        normalized_references.append(
            _normalize_evidence_ref(
                reference,
                source_type=normalized_ref_source_type(reference),
                item_confidence=item_confidence,
                fallback_excerpt=fallback_excerpt,
            )
        )
    return normalized_references



def _normalize_evidence_ref(
    reference: Any,
    *,
    source_type: str | None,
    item_confidence: float,
    fallback_excerpt: str,
) -> Any:
    if not isinstance(reference, Mapping):
        return {
            "sourceType": "chapters",
            "sourceSpan": {"spanRef": "model_inferred_span"},
            "excerpt": fallback_excerpt,
            "observationType": "narrative_observation",
            "evidenceNote": "由真实 provider 返回内容归一化补全。",
            "confidence": item_confidence,
        }
    normalized_reference: dict[str, Any] = dict(reference)
    normalized_reference["sourceType"] = _normalize_source_type(source_type)
    source_span = normalized_reference.get("sourceSpan")
    if isinstance(source_span, Mapping):
        normalized_reference["sourceSpan"] = dict(source_span)
    elif isinstance(source_span, str) and source_span.strip():
        span_key = _SOURCE_SPAN_KEYS.get(source_type or "", "spanRef")
        normalized_reference["sourceSpan"] = {span_key: source_span.strip()}
    else:
        normalized_reference["sourceSpan"] = {"spanRef": "model_inferred_span"}
    excerpt = normalized_text_value(normalized_reference.get("excerpt"))
    if excerpt is None:
        excerpt = normalized_text_value(normalized_reference.get("reference"))
    normalized_reference["excerpt"] = excerpt or fallback_excerpt
    normalized_reference["observationType"] = (
        normalized_text_value(normalized_reference.get("observationType")) or "narrative_observation"
    )
    normalized_reference["evidenceNote"] = (
        normalized_text_value(normalized_reference.get("evidenceNote")) or "由真实 provider 返回内容归一化补全。"
    )
    normalized_reference["confidence"] = _normalize_confidence(
        normalized_reference.get("confidence"),
        fallback=item_confidence,
    )
    normalized_reference.pop("reference", None)
    return normalized_reference



def _normalize_skeleton_dimensions(raw_dimensions: Any, *, axis_key: str | None) -> list[str]:
    normalized_dimensions: list[str] = []
    if isinstance(raw_dimensions, list):
        for value in raw_dimensions:
            if not isinstance(value, str):
                continue
            normalized_value = _SKELETON_DIMENSION_ALIASES.get(value.strip())
            if normalized_value and normalized_value not in normalized_dimensions:
                normalized_dimensions.append(normalized_value)
    if normalized_dimensions:
        return normalized_dimensions
    default_dimension = _DEFAULT_SKELETON_DIMENSIONS_BY_AXIS.get(axis_key or "")
    return [default_dimension] if default_dimension is not None else []



def _normalize_axis_summaries(
    *,
    raw_axis_summaries: Any,
    normalized_items: Any,
) -> dict[str, str]:
    normalized_summaries: dict[str, str] = {}
    if isinstance(raw_axis_summaries, Mapping):
        for raw_axis_id, raw_summary in raw_axis_summaries.items():
            axis_key = _normalize_axis_key(raw_axis_id)
            if axis_key is None:
                continue
            summary_text = _extract_summary_text(raw_summary)
            if summary_text is not None:
                normalized_summaries[axis_key] = summary_text
    elif isinstance(raw_axis_summaries, list):
        for raw_summary in raw_axis_summaries:
            if not isinstance(raw_summary, Mapping):
                continue
            axis_key = _normalize_axis_key(raw_summary.get("axisId"))
            if axis_key is None:
                continue
            summary_text = _extract_summary_text(raw_summary)
            if summary_text is not None:
                normalized_summaries[axis_key] = summary_text
    if isinstance(normalized_items, list):
        for item in normalized_items:
            if not isinstance(item, Mapping):
                continue
            axis_key = _normalize_axis_key(item.get("axisId"))
            reason = item.get("reason")
            if axis_key is None or not isinstance(reason, str) or not reason.strip():
                continue
            normalized_summaries.setdefault(axis_key, reason.strip())
    return normalized_summaries



def _extract_summary_text(raw_summary: Any) -> str | None:
    if isinstance(raw_summary, str):
        stripped = raw_summary.strip()
        return stripped or None
    if not isinstance(raw_summary, Mapping):
        return None
    parts: list[str] = []
    summary = raw_summary.get("summary")
    if isinstance(summary, str) and summary.strip():
        parts.append(summary.strip())
    strengths = _normalize_text_list(raw_summary.get("strengths"))
    if strengths:
        parts.append(f"优势：{'、'.join(strengths)}")
    weaknesses = _normalize_text_list(raw_summary.get("weaknesses"))
    if weaknesses:
        parts.append(f"弱点：{'、'.join(weaknesses)}")
    reason = raw_summary.get("reason")
    if isinstance(reason, str) and reason.strip():
        parts.append(reason.strip())
    return "；".join(parts) if parts else None



def _normalize_axis_ids(raw_axis_ids: Any) -> list[str]:
    if not isinstance(raw_axis_ids, list):
        return []
    normalized_axis_ids: list[str] = []
    for value in raw_axis_ids:
        axis_key = _normalize_axis_key(value)
        if axis_key is not None and axis_key not in normalized_axis_ids:
            normalized_axis_ids.append(axis_key)
    return normalized_axis_ids



def _normalize_risk_tags(raw_risk_tags: Any) -> list[str]:
    if not isinstance(raw_risk_tags, list):
        return []
    allowed_risk_tags = {risk.value for risk in FatalRisk}
    normalized_risk_tags: list[str] = []
    for value in raw_risk_tags:
        if not isinstance(value, str):
            continue
        normalized_value = value.strip()
        if normalized_value in allowed_risk_tags and normalized_value not in normalized_risk_tags:
            normalized_risk_tags.append(normalized_value)
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



def _normalize_axis_key(raw_axis_id: Any) -> str | None:
    if isinstance(raw_axis_id, AxisId):
        return raw_axis_id.value
    if not isinstance(raw_axis_id, str):
        return None
    stripped = raw_axis_id.strip()
    return stripped if stripped in {axis.value for axis in AxisId} else None



def _normalize_source_type(raw_source_type: str | None) -> str:
    if raw_source_type in _SOURCE_SPAN_KEYS:
        return raw_source_type
    return "chapters"



def _normalize_score_band(raw_score_band: Any) -> str:
    if isinstance(raw_score_band, int) and 0 <= raw_score_band <= 4:
        return str(raw_score_band)
    if not isinstance(raw_score_band, str):
        return ScoreBand.TWO.value
    return _SCORE_BAND_ALIASES.get(raw_score_band.strip(), ScoreBand.TWO.value)



def _normalize_confidence(raw_value: Any, *, fallback: float) -> float:
    if isinstance(raw_value, int | float):
        value = float(raw_value)
        if 0 <= value <= 1:
            return value
    return fallback



def normalized_text_value(raw_value: Any) -> str | None:
    if not isinstance(raw_value, str):
        return None
    stripped = raw_value.strip()
    return stripped or None
