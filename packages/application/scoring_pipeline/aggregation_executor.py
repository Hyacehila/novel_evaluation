from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.scoring_pipeline.exceptions import PipelineFailureError
from packages.application.scoring_pipeline.models import AggregationExecutionContext
from packages.application.scoring_pipeline.provider_support import execute_provider_stage
from packages.application.support.process_logging import log_event
from packages.schemas.common.enums import AxisId, FatalRisk, ScoreBand, SkeletonDimensionId, StageName, TopLevelScoreField
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.result import DetailedAnalysis
from packages.schemas.stages.aggregation import AggregatedRubricResult

logger = logging.getLogger(__name__)

_STAGE_TIMEOUT_MS = 90_000
_STAGE_MAX_TOKENS = 4_000
_DEFAULT_SUPPORTING_AXIS_MAP = {
    TopLevelScoreField.SIGNING_PROBABILITY.value: [
        AxisId.PLATFORM_FIT.value,
        AxisId.COMMERCIAL_POTENTIAL.value,
    ],
    TopLevelScoreField.COMMERCIAL_VALUE.value: [
        AxisId.COMMERCIAL_POTENTIAL.value,
        AxisId.SERIAL_MOMENTUM.value,
    ],
    TopLevelScoreField.WRITING_QUALITY.value: [
        AxisId.NARRATIVE_CONTROL.value,
        AxisId.PACING_PAYOFF.value,
    ],
    TopLevelScoreField.INNOVATION_SCORE.value: [
        AxisId.SETTING_DIFFERENTIATION.value,
        AxisId.HOOK_RETENTION.value,
    ],
}
_DEFAULT_SUPPORTING_SKELETON_MAP = {
    TopLevelScoreField.SIGNING_PROBABILITY.value: [SkeletonDimensionId.MARKET_ATTRACTION.value],
    TopLevelScoreField.COMMERCIAL_VALUE.value: [
        SkeletonDimensionId.MARKET_ATTRACTION.value,
        SkeletonDimensionId.CHARACTER_MOMENTUM.value,
    ],
    TopLevelScoreField.WRITING_QUALITY.value: [SkeletonDimensionId.NARRATIVE_EXECUTION.value],
    TopLevelScoreField.INNOVATION_SCORE.value: [SkeletonDimensionId.NOVELTY_UTILITY.value],
}
_AXIS_TO_SKELETON_DIMENSION = {
    AxisId.HOOK_RETENTION.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
    AxisId.SERIAL_MOMENTUM.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
    AxisId.CHARACTER_DRIVE.value: SkeletonDimensionId.CHARACTER_MOMENTUM.value,
    AxisId.NARRATIVE_CONTROL.value: SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    AxisId.PACING_PAYOFF.value: SkeletonDimensionId.NARRATIVE_EXECUTION.value,
    AxisId.SETTING_DIFFERENTIATION.value: SkeletonDimensionId.NOVELTY_UTILITY.value,
    AxisId.PLATFORM_FIT.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
    AxisId.COMMERCIAL_POTENTIAL.value: SkeletonDimensionId.MARKET_ATTRACTION.value,
}
_SCORE_BAND_TO_PERCENTAGE = {
    ScoreBand.ZERO.value: 20,
    ScoreBand.ONE.value: 35,
    ScoreBand.TWO.value: 55,
    ScoreBand.THREE.value: 75,
    ScoreBand.FOUR.value: 90,
}


def execute_aggregation(
    *,
    provider_adapter: ProviderExecutionPort,
    context: AggregationExecutionContext,
) -> AggregatedRubricResult:
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
        user_payload={
            "taskId": context.task_id,
            "title": context.submission.title,
            "chapters": [chapter.content for chapter in context.submission.chapters or []],
            "outline": context.submission.outline.content if context.submission.outline is not None else None,
            "screening": context.screening.model_dump(mode="json"),
            "rubric": context.rubric.model_dump(mode="json"),
            "consistency": context.consistency.model_dump(mode="json"),
        },
    )
    payload = _normalize_aggregation_payload(payload=payload, context=context)
    try:
        return AggregatedRubricResult.model_validate(payload)
    except Exception as exc:  # noqa: BLE001
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
    normalized_payload.update(
        {
            "taskId": context.task_id,
            "stage": StageName.AGGREGATION.value,
            "schemaVersion": context.binding.schema_version,
            "promptVersion": context.binding.prompt_version,
            "rubricVersion": context.binding.rubric_version,
            "providerId": context.binding.provider_id,
            "modelId": context.binding.model_id,
        }
    )
    if not any(
        key in normalized_payload
        for key in (
            "axisScores",
            "skeletonScores",
            "topLevelScoresDraft",
            "strengthCandidates",
            "weaknessCandidates",
            "platformCandidates",
            "marketFitDraft",
            "editorVerdictDraft",
            "detailedAnalysisDraft",
        )
    ):
        return normalized_payload
    axis_scores = _normalize_axis_scores(normalized_payload.get("axisScores"), context=context)
    skeleton_scores = _normalize_skeleton_scores(
        normalized_payload.get("skeletonScores"),
        axis_scores=axis_scores,
    )
    normalized_payload.update(
        {
            "axisScores": axis_scores,
            "skeletonScores": skeleton_scores,
            "topLevelScoresDraft": _normalize_top_level_scores(
                raw_scores=normalized_payload.get("topLevelScoresDraft"),
                axis_scores=axis_scores,
            ),
            "strengthCandidates": _normalize_text_list(normalized_payload.get("strengthCandidates")),
            "weaknessCandidates": _normalize_text_list(normalized_payload.get("weaknessCandidates")),
            "platformCandidates": _normalize_text_list(normalized_payload.get("platformCandidates")),
            "marketFitDraft": _normalize_text_value(normalized_payload.get("marketFitDraft"))
            or "当前材料可形成初步市场判断，但仍建议结合完整正文复核。",
            "editorVerdictDraft": _normalize_text_value(normalized_payload.get("editorVerdictDraft"))
            or "当前可作为保守判断结果，建议补充完整正文后复核。",
            "detailedAnalysisDraft": _normalize_detailed_analysis(normalized_payload.get("detailedAnalysisDraft")),
            "supportingAxisMap": _normalize_supporting_axis_map(normalized_payload.get("supportingAxisMap")),
            "supportingSkeletonMap": _normalize_supporting_skeleton_map(normalized_payload.get("supportingSkeletonMap")),
            "riskTags": _normalize_risk_tags(normalized_payload.get("riskTags")),
            "overallConfidence": _normalize_confidence(
                normalized_payload.get("overallConfidence"),
                fallback=context.consistency.confidence,
            ),
        }
    )
    return normalized_payload


def _normalize_axis_scores(raw_scores: Any, *, context: AggregationExecutionContext) -> dict[str, int]:
    normalized_scores: dict[str, int] = {}
    if isinstance(raw_scores, Mapping):
        for axis in AxisId:
            normalized_value = _normalize_percentage(raw_scores.get(axis.value))
            if normalized_value is not None:
                normalized_scores[axis.value] = normalized_value
    if len(normalized_scores) == len(AxisId):
        return normalized_scores
    rubric_fallback_scores = {
        item.axisId.value: _SCORE_BAND_TO_PERCENTAGE.get(item.scoreBand.value, 55)
        for item in context.rubric.items
    }
    for axis in AxisId:
        normalized_scores.setdefault(axis.value, rubric_fallback_scores.get(axis.value, 55))
    return normalized_scores


def _normalize_skeleton_scores(raw_scores: Any, *, axis_scores: Mapping[str, int]) -> dict[str, int]:
    normalized_scores: dict[str, int] = {}
    if isinstance(raw_scores, Mapping):
        for dimension in SkeletonDimensionId:
            normalized_value = _normalize_percentage(raw_scores.get(dimension.value))
            if normalized_value is not None:
                normalized_scores[dimension.value] = normalized_value
    if len(normalized_scores) == len(SkeletonDimensionId):
        return normalized_scores
    grouped_scores: dict[str, list[int]] = {dimension.value: [] for dimension in SkeletonDimensionId}
    for axis_key, score in axis_scores.items():
        grouped_scores[_AXIS_TO_SKELETON_DIMENSION[axis_key]].append(score)
    for dimension in SkeletonDimensionId:
        scores = grouped_scores[dimension.value]
        normalized_scores.setdefault(
            dimension.value,
            round(sum(scores) / len(scores)) if scores else 55,
        )
    return normalized_scores


def _normalize_top_level_scores(
    *,
    raw_scores: Any,
    axis_scores: Mapping[str, int],
) -> dict[str, int]:
    normalized_scores: dict[str, int] = {}
    if isinstance(raw_scores, Mapping):
        for field in TopLevelScoreField:
            normalized_value = _normalize_percentage(raw_scores.get(field.value))
            if normalized_value is not None:
                normalized_scores[field.value] = normalized_value
    for field_key, axis_keys in _DEFAULT_SUPPORTING_AXIS_MAP.items():
        normalized_scores.setdefault(
            field_key,
            round(sum(axis_scores[axis_key] for axis_key in axis_keys) / len(axis_keys)),
        )
    return normalized_scores


def _normalize_detailed_analysis(raw_analysis: Any) -> dict[str, str]:
    if isinstance(raw_analysis, Mapping):
        plot = _normalize_text_value(raw_analysis.get("plot"))
        character = _normalize_text_value(raw_analysis.get("character"))
        pacing = _normalize_text_value(raw_analysis.get("pacing"))
        world_building = _normalize_text_value(raw_analysis.get("worldBuilding"))
        fallback = plot or character or pacing or world_building or "当前阶段仅形成保守分析摘要。"
        return DetailedAnalysis(
            plot=plot or fallback,
            character=character or fallback,
            pacing=pacing or fallback,
            worldBuilding=world_building or fallback,
        ).model_dump(mode="json")
    summary = _normalize_text_value(raw_analysis) or "当前阶段仅形成保守分析摘要。"
    return DetailedAnalysis(
        plot=summary,
        character=summary,
        pacing=summary,
        worldBuilding=summary,
    ).model_dump(mode="json")


def _normalize_supporting_axis_map(raw_map: Any) -> dict[str, list[str]]:
    normalized_map: dict[str, list[str]] = {}
    if isinstance(raw_map, Mapping):
        for field in TopLevelScoreField:
            raw_values = raw_map.get(field.value)
            if not isinstance(raw_values, list):
                continue
            normalized_values = _normalize_axis_values(raw_values)
            if normalized_values:
                normalized_map[field.value] = normalized_values
    for field_key, default_values in _DEFAULT_SUPPORTING_AXIS_MAP.items():
        normalized_map.setdefault(field_key, list(default_values))
    return normalized_map


def _normalize_supporting_skeleton_map(raw_map: Any) -> dict[str, list[str]]:
    normalized_map: dict[str, list[str]] = {}
    if isinstance(raw_map, Mapping):
        for field in TopLevelScoreField:
            raw_values = raw_map.get(field.value)
            if not isinstance(raw_values, list):
                continue
            normalized_values = _normalize_skeleton_values(raw_values)
            if normalized_values:
                normalized_map[field.value] = normalized_values
    for field_key, default_values in _DEFAULT_SUPPORTING_SKELETON_MAP.items():
        normalized_map.setdefault(field_key, list(default_values))
    return normalized_map


def _normalize_axis_values(raw_values: list[Any]) -> list[str]:
    normalized_values: list[str] = []
    allowed_values = {axis.value for axis in AxisId}
    for value in raw_values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if stripped in allowed_values and stripped not in normalized_values:
            normalized_values.append(stripped)
    return normalized_values


def _normalize_skeleton_values(raw_values: list[Any]) -> list[str]:
    normalized_values: list[str] = []
    allowed_values = {dimension.value for dimension in SkeletonDimensionId}
    for value in raw_values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if stripped in allowed_values and stripped not in normalized_values:
            normalized_values.append(stripped)
    return normalized_values


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
        text_value = _normalize_text_value(value)
        if text_value is not None:
            normalized_values.append(text_value)
    return normalized_values


def _normalize_text_value(raw_value: Any) -> str | None:
    if not isinstance(raw_value, str):
        return None
    stripped = raw_value.strip()
    return stripped or None


def _normalize_percentage(raw_value: Any) -> int | None:
    if isinstance(raw_value, int):
        return min(100, max(0, raw_value))
    if isinstance(raw_value, float) and raw_value.is_integer():
        return min(100, max(0, int(raw_value)))
    return None


def _normalize_confidence(raw_value: Any, *, fallback: float) -> float:
    if isinstance(raw_value, int | float):
        value = float(raw_value)
        if 0 <= value <= 1:
            return value
    return fallback
