from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.scoring_pipeline.exceptions import PipelineFailureError
from packages.application.scoring_pipeline.models import TypeLensExecutionContext
from packages.application.scoring_pipeline.provider_support import execute_provider_stage
from packages.application.scoring_pipeline.type_support import build_type_lens_summary
from packages.schemas.common.enums import EvaluationMode, FatalRisk, ScoreBand, StageName
from packages.schemas.common.novel_types import get_novel_type_label, get_type_lens_definitions
from packages.schemas.output.error import ErrorCode
from packages.schemas.stages.type_lens import TypeLensEvaluationResult
from packages.runtime.logging import log_event

logger = logging.getLogger(__name__)

_STAGE_TIMEOUT_MS = 90_000
_STAGE_MAX_TOKENS = 4_000
_SCHEMA_VALIDATION_MAX_ATTEMPTS = 2
_SCORE_BAND_ALIASES = {
    ScoreBand.ZERO.value: ScoreBand.ZERO.value,
    ScoreBand.ONE.value: ScoreBand.ONE.value,
    ScoreBand.TWO.value: ScoreBand.TWO.value,
    ScoreBand.THREE.value: ScoreBand.THREE.value,
    ScoreBand.FOUR.value: ScoreBand.FOUR.value,
    "very_low": ScoreBand.ZERO.value,
    "low": ScoreBand.ONE.value,
    "medium": ScoreBand.TWO.value,
    "medium_high": ScoreBand.THREE.value,
    "high": ScoreBand.FOUR.value,
    "弱": ScoreBand.ONE.value,
    "中": ScoreBand.TWO.value,
    "高": ScoreBand.FOUR.value,
}
_SOURCE_SPAN_KEYS = {
    "chapters": "chapterRef",
    "outline": "outlineRef",
    "cross_input": "crossInputRef",
}


def execute_type_lens(
    *,
    provider_adapter: ProviderExecutionPort,
    context: TypeLensExecutionContext,
) -> TypeLensEvaluationResult:
    lens_definitions = get_type_lens_definitions(context.type_classification.novelType)
    user_payload = {
        "taskId": context.task_id,
        "title": context.submission.title,
        "inputComposition": context.screening.inputComposition.value,
        "evaluationMode": context.screening.evaluationMode.value,
        "chapters": [chapter.content for chapter in context.submission.chapters or []],
        "outline": context.submission.outline.content if context.submission.outline is not None else None,
        "screening": context.screening.model_dump(mode="json"),
        "typeClassification": context.type_classification.model_dump(mode="json"),
        "selectedType": {
            "novelType": context.type_classification.novelType.value,
            "label": get_novel_type_label(context.type_classification.novelType),
            "lenses": [
                {"lensId": definition.lens_id, "label": definition.label}
                for definition in lens_definitions
            ],
        },
    }
    for attempt in range(1, _SCHEMA_VALIDATION_MAX_ATTEMPTS + 1):
        payload = execute_provider_stage(
            provider_adapter=provider_adapter,
            binding=context.binding,
            task_id=context.task_id,
            stage=StageName.TYPE_LENS_EVALUATION,
            input_composition=context.screening.inputComposition,
            evaluation_mode=context.screening.evaluationMode,
            timeout_ms=_STAGE_TIMEOUT_MS,
            max_tokens=_STAGE_MAX_TOKENS,
            response_format={"type": "json_object"},
            user_payload=user_payload,
        )
        payload = _normalize_type_lens_payload(payload=payload, context=context)
        try:
            return TypeLensEvaluationResult.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            if attempt < _SCHEMA_VALIDATION_MAX_ATTEMPTS:
                log_event(
                    logger,
                    logging.WARNING,
                    "stage_schema_invalid_retry",
                    taskId=context.task_id,
                    stage=StageName.TYPE_LENS_EVALUATION,
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
                stage=StageName.TYPE_LENS_EVALUATION,
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
                message="type_lens_evaluation 阶段输出不满足正式 schema。",
            ) from exc


def _normalize_type_lens_payload(*, payload: Any, context: TypeLensExecutionContext) -> Any:
    if not isinstance(payload, Mapping):
        return payload
    lens_definitions = get_type_lens_definitions(context.type_classification.novelType)
    raw_items = payload.get("items") or payload.get("lenses")
    normalized_items = [
        _normalize_type_lens_item(
            raw_item=_find_matching_lens_item(raw_items, lens_id=definition.lens_id, label=definition.label),
            lens_id=definition.lens_id,
            label=definition.label,
            degraded_default=context.screening.evaluationMode is EvaluationMode.DEGRADED,
        )
        for definition in lens_definitions
    ]
    summary = _normalize_text_value(payload.get("summary")) or build_type_lens_summary(
        novel_type=context.type_classification.novelType
    )
    normalized_payload = {
        "taskId": context.task_id,
        "stage": StageName.TYPE_LENS_EVALUATION.value,
        "schemaVersion": context.binding.schema_version,
        "promptVersion": context.binding.prompt_version,
        "rubricVersion": context.binding.rubric_version,
        "providerId": context.binding.provider_id,
        "modelId": context.binding.model_id,
        "inputComposition": context.screening.inputComposition.value,
        "evaluationMode": context.screening.evaluationMode.value,
        "novelType": context.type_classification.novelType.value,
        "summary": summary,
        "items": normalized_items,
        "overallConfidence": _normalize_confidence(
            payload.get("overallConfidence"),
            fallback=min(item["confidence"] for item in normalized_items),
        ),
    }
    return normalized_payload


def _find_matching_lens_item(raw_items: Any, *, lens_id: str, label: str) -> Any:
    if not isinstance(raw_items, list):
        return None
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        raw_lens_id = item.get("lensId")
        raw_label = item.get("label")
        if isinstance(raw_lens_id, str) and raw_lens_id.strip() == lens_id:
            return item
        if isinstance(raw_label, str) and raw_label.strip() == label:
            return item
    return None


def _normalize_type_lens_item(
    *,
    raw_item: Any,
    lens_id: str,
    label: str,
    degraded_default: bool,
) -> dict[str, Any]:
    normalized_item = dict(raw_item) if isinstance(raw_item, Mapping) else {}
    item_confidence = _normalize_confidence(
        normalized_item.get("confidence"),
        fallback=0.58 if degraded_default else 0.76,
    )
    reason = _normalize_text_value(normalized_item.get("reason"))
    if reason is None:
        reason = f"{label} 当前证据仍偏有限，后端按固定 lens 输出保守占位结论。"
    return {
        "lensId": lens_id,
        "label": label,
        "scoreBand": _normalize_score_band(normalized_item.get("scoreBand")),
        "reason": reason,
        "evidenceRefs": _normalize_evidence_refs(
            normalized_item.get("evidenceRefs"),
            fallback_excerpt=reason,
            item_confidence=item_confidence,
        ),
        "confidence": item_confidence,
        "riskTags": _normalize_risk_tags(normalized_item.get("riskTags")),
        "degradedByInput": _normalize_bool(normalized_item.get("degradedByInput"), fallback=degraded_default),
    }


def _normalize_evidence_refs(raw_references: Any, *, fallback_excerpt: str, item_confidence: float) -> list[dict[str, Any]]:
    if not isinstance(raw_references, list) or not raw_references:
        return [
            {
                "sourceType": "chapters",
                "sourceSpan": {"spanRef": "model_inferred_span"},
                "excerpt": fallback_excerpt,
                "observationType": "narrative_observation",
                "evidenceNote": "由 type lens 阶段归一化补全的保守证据。",
                "confidence": item_confidence,
            }
        ]
    return [
        _normalize_evidence_ref(reference, fallback_excerpt=fallback_excerpt, item_confidence=item_confidence)
        for reference in raw_references
    ]


def _normalize_evidence_ref(reference: Any, *, fallback_excerpt: str, item_confidence: float) -> dict[str, Any]:
    if not isinstance(reference, Mapping):
        return {
            "sourceType": "chapters",
            "sourceSpan": {"spanRef": "model_inferred_span"},
            "excerpt": fallback_excerpt,
            "observationType": "narrative_observation",
            "evidenceNote": "由 type lens 阶段归一化补全的保守证据。",
            "confidence": item_confidence,
        }
    normalized_reference = dict(reference)
    source_type = _normalize_source_type(normalized_reference.get("sourceType"))
    source_span = normalized_reference.get("sourceSpan")
    if isinstance(source_span, Mapping):
        normalized_source_span = dict(source_span)
    elif isinstance(source_span, str) and source_span.strip():
        normalized_source_span = {_SOURCE_SPAN_KEYS.get(source_type, "spanRef"): source_span.strip()}
    else:
        normalized_source_span = {"spanRef": "model_inferred_span"}
    return {
        "sourceType": source_type,
        "sourceSpan": normalized_source_span,
        "excerpt": _normalize_text_value(normalized_reference.get("excerpt")) or fallback_excerpt,
        "observationType": _normalize_text_value(normalized_reference.get("observationType")) or "narrative_observation",
        "evidenceNote": _normalize_text_value(normalized_reference.get("evidenceNote")) or "由 type lens 阶段归一化补全的保守证据。",
        "confidence": _normalize_confidence(normalized_reference.get("confidence"), fallback=item_confidence),
    }


def _normalize_score_band(raw_value: Any) -> str:
    if isinstance(raw_value, int) and 0 <= raw_value <= 4:
        return str(raw_value)
    if isinstance(raw_value, str):
        return _SCORE_BAND_ALIASES.get(raw_value.strip(), ScoreBand.TWO.value)
    return ScoreBand.TWO.value


def _normalize_source_type(raw_value: Any) -> str:
    if isinstance(raw_value, str) and raw_value.strip() in _SOURCE_SPAN_KEYS:
        return raw_value.strip()
    return "chapters"


def _normalize_risk_tags(raw_values: Any) -> list[str]:
    if not isinstance(raw_values, list):
        return []
    allowed_risk_tags = {risk.value for risk in FatalRisk}
    normalized_values: list[str] = []
    for value in raw_values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if stripped in allowed_risk_tags and stripped not in normalized_values:
            normalized_values.append(stripped)
    return normalized_values


def _normalize_confidence(raw_value: Any, *, fallback: float) -> float:
    if isinstance(raw_value, int | float):
        value = float(raw_value)
        if 0 <= value <= 1:
            return value
    return fallback


def _normalize_text_value(raw_value: Any) -> str | None:
    if not isinstance(raw_value, str):
        return None
    stripped = raw_value.strip()
    return stripped or None


def _normalize_bool(raw_value: Any, *, fallback: bool) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    return fallback
