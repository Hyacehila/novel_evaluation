from __future__ import annotations

from packages.schemas.common.enums import AxisId, EvaluationMode, ScoreBand
from packages.schemas.output.result import AxisEvaluationResult, FinalEvaluationProjection, OverallEvaluationResult
from packages.schemas.stages.aggregation import AggregatedRubricResult
from packages.schemas.stages.consistency import ConflictType, ConsistencyCheckResult
from packages.schemas.stages.rubric import RubricEvaluationSet


_SCORE_BAND_TO_SCORE = {
    ScoreBand.ZERO: 20,
    ScoreBand.ONE: 35,
    ScoreBand.TWO: 55,
    ScoreBand.THREE: 75,
    ScoreBand.FOUR: 90,
}


def build_final_projection(
    *,
    aggregation: AggregatedRubricResult,
    rubric: RubricEvaluationSet,
    consistency: ConsistencyCheckResult,
) -> FinalEvaluationProjection:
    item_by_axis = {item.axisId: item for item in rubric.items}
    axes = [
        AxisEvaluationResult(
            axisId=axis_id,
            scoreBand=item_by_axis[axis_id].scoreBand,
            score=_SCORE_BAND_TO_SCORE[item_by_axis[axis_id].scoreBand],
            summary=rubric.axisSummaries[axis_id],
            reason=item_by_axis[axis_id].reason,
            degradedByInput=item_by_axis[axis_id].degradedByInput,
            riskTags=list(item_by_axis[axis_id].riskTags),
        )
        for axis_id in AxisId
    ]
    overall = OverallEvaluationResult(
        score=_build_overall_score(axes=axes, rubric=rubric, consistency=consistency),
        verdict=aggregation.overallVerdictDraft,
        summary=aggregation.overallSummaryDraft,
        platformCandidates=aggregation.platformCandidates,
        marketFit=aggregation.marketFitDraft,
    )
    return FinalEvaluationProjection(
        taskId=aggregation.taskId,
        schemaVersion=aggregation.schemaVersion,
        promptVersion=aggregation.promptVersion,
        rubricVersion=aggregation.rubricVersion,
        providerId=aggregation.providerId,
        modelId=aggregation.modelId,
        axes=axes,
        overall=overall,
    )


def _build_overall_score(
    *,
    axes: list[AxisEvaluationResult],
    rubric: RubricEvaluationSet,
    consistency: ConsistencyCheckResult,
) -> int:
    base_score = round(sum(axis.score for axis in axes) / len(axes))
    if rubric.evaluationMode is EvaluationMode.DEGRADED:
        base_score -= 8
    if consistency.duplicatedPenaltiesDetected:
        base_score -= 3
    if any(conflict.conflictType is ConflictType.WEAK_EVIDENCE for conflict in consistency.conflicts):
        base_score -= 4
    return max(0, min(100, base_score))
