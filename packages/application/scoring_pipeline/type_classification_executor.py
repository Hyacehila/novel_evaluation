from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.scoring_pipeline.exceptions import PipelineFailureError
from packages.application.scoring_pipeline.models import TypeClassificationExecutionContext
from packages.application.scoring_pipeline.provider_support import execute_provider_stage
from packages.application.scoring_pipeline.type_support import (
    build_type_classification_summary,
    select_final_novel_type,
)
from packages.application.support.process_logging import log_event
from packages.schemas.common.enums import NovelType, StageName
from packages.schemas.common.novel_types import build_type_lens_catalog_payload, get_novel_type_label
from packages.schemas.output.error import ErrorCode
from packages.schemas.stages.type_classification import TypeClassificationCandidate, TypeClassificationResult

logger = logging.getLogger(__name__)

_STAGE_TIMEOUT_MS = 90_000
_STAGE_MAX_TOKENS = 2_500
_SCHEMA_VALIDATION_MAX_ATTEMPTS = 2
_FALLBACK_CANDIDATE_CONFIDENCES = (0.55, 0.43, 0.31)


def execute_type_classification(
    *,
    provider_adapter: ProviderExecutionPort,
    context: TypeClassificationExecutionContext,
) -> TypeClassificationResult:
    user_payload = {
        "taskId": context.task_id,
        "title": context.submission.title,
        "inputComposition": context.screening.inputComposition.value,
        "evaluationMode": context.screening.evaluationMode.value,
        "chapters": [chapter.content for chapter in context.submission.chapters or []],
        "outline": context.submission.outline.content if context.submission.outline is not None else None,
        "screening": context.screening.model_dump(mode="json"),
        "novelTypeCatalog": build_type_lens_catalog_payload(),
        "decisionPolicy": {
            "minConfidence": 0.60,
            "minMargin": 0.12,
            "fallbackType": NovelType.GENERAL_FALLBACK.value,
            "femaleGeneralIsTerminal": True,
        },
    }
    for attempt in range(1, _SCHEMA_VALIDATION_MAX_ATTEMPTS + 1):
        payload = execute_provider_stage(
            provider_adapter=provider_adapter,
            binding=context.binding,
            task_id=context.task_id,
            stage=StageName.TYPE_CLASSIFICATION,
            input_composition=context.screening.inputComposition,
            evaluation_mode=context.screening.evaluationMode,
            timeout_ms=_STAGE_TIMEOUT_MS,
            max_tokens=_STAGE_MAX_TOKENS,
            response_format={"type": "json_object"},
            user_payload=user_payload,
        )
        payload = _normalize_type_classification_payload(payload=payload, context=context)
        try:
            return TypeClassificationResult.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            if attempt < _SCHEMA_VALIDATION_MAX_ATTEMPTS:
                log_event(
                    logger,
                    logging.WARNING,
                    "stage_schema_invalid_retry",
                    taskId=context.task_id,
                    stage=StageName.TYPE_CLASSIFICATION,
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
                stage=StageName.TYPE_CLASSIFICATION,
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
                message="type_classification 阶段输出不满足正式 schema。",
            ) from exc


def _normalize_type_classification_payload(
    *,
    payload: Any,
    context: TypeClassificationExecutionContext,
) -> Any:
    if not isinstance(payload, Mapping):
        return payload
    normalized_payload = dict(payload)
    candidates = _normalize_candidates(normalized_payload.get("candidates"))
    decision = select_final_novel_type(candidates)
    summary = _normalize_text_value(normalized_payload.get("summary"))
    if summary is None:
        summary = build_type_classification_summary(
            selected_type=decision.novel_type,
            candidates=candidates,
            fallback_used=decision.fallback_used,
        )
    normalized_payload.update(
        {
            "taskId": context.task_id,
            "stage": StageName.TYPE_CLASSIFICATION.value,
            "schemaVersion": context.binding.schema_version,
            "promptVersion": context.binding.prompt_version,
            "rubricVersion": context.binding.rubric_version,
            "providerId": context.binding.provider_id,
            "modelId": context.binding.model_id,
            "inputComposition": context.screening.inputComposition.value,
            "evaluationMode": context.screening.evaluationMode.value,
            "candidates": [candidate.model_dump(mode="json") for candidate in candidates],
            "novelType": decision.novel_type.value,
            "classificationConfidence": decision.classification_confidence,
            "fallbackUsed": decision.fallback_used,
            "summary": summary,
        }
    )
    return normalized_payload


def _normalize_candidates(raw_candidates: Any) -> list[TypeClassificationCandidate]:
    candidates: list[TypeClassificationCandidate] = []
    if isinstance(raw_candidates, list):
        for index, item in enumerate(raw_candidates):
            candidate = _normalize_candidate(item, index=index)
            if candidate is None or any(existing.novelType is candidate.novelType for existing in candidates):
                continue
            candidates.append(candidate)
            if len(candidates) == 3:
                break
    if len(candidates) < 3:
        for novel_type in NovelType:
            if any(existing.novelType is novel_type for existing in candidates):
                continue
            fallback_index = len(candidates)
            candidates.append(
                TypeClassificationCandidate(
                    novelType=novel_type,
                    confidence=_FALLBACK_CANDIDATE_CONFIDENCES[min(fallback_index, len(_FALLBACK_CANDIDATE_CONFIDENCES) - 1)],
                    reason=f"模型未稳定给出“{get_novel_type_label(novel_type)}”候选，后端使用兜底候选补全 Top-3。",
                )
            )
            if len(candidates) == 3:
                break
    return candidates[:3]


def _normalize_candidate(item: Any, *, index: int) -> TypeClassificationCandidate | None:
    if not isinstance(item, Mapping):
        return None
    novel_type = _normalize_novel_type(item.get("novelType") or item.get("type") or item.get("label"))
    if novel_type is None:
        return None
    confidence = _normalize_confidence(
        item.get("confidence"),
        fallback=_FALLBACK_CANDIDATE_CONFIDENCES[min(index, len(_FALLBACK_CANDIDATE_CONFIDENCES) - 1)],
    )
    reason = _normalize_text_value(item.get("reason")) or f"当前样本具备“{get_novel_type_label(novel_type)}”的显著题材信号。"
    return TypeClassificationCandidate(
        novelType=novel_type,
        confidence=confidence,
        reason=reason,
    )


def _normalize_novel_type(raw_value: Any) -> NovelType | None:
    if isinstance(raw_value, NovelType):
        return raw_value
    if not isinstance(raw_value, str):
        return None
    stripped = raw_value.strip()
    for novel_type in NovelType:
        if stripped == novel_type.value:
            return novel_type
    return None


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
