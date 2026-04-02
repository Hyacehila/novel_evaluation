from __future__ import annotations

from packages.schemas.common.enums import AxisId, EvaluationMode, NovelType, ScoreBand
from packages.schemas.output.result import (
    AxisEvaluationResult,
    FinalEvaluationProjection,
    OverallEvaluationResult,
    TypeAssessmentResult,
)
from packages.schemas.stages.aggregation import AggregatedRubricResult
from packages.schemas.stages.consistency import ConflictType, ConsistencyCheckResult
from packages.schemas.stages.rubric import RubricEvaluationSet
from packages.schemas.stages.type_classification import TypeClassificationResult
from packages.schemas.stages.type_lens import TypeLensEvaluationResult


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
    type_classification: TypeClassificationResult,
    rubric: RubricEvaluationSet,
    type_lens: TypeLensEvaluationResult,
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
        score=_build_overall_score(
            axes=axes,
            rubric=rubric,
            consistency=consistency,
            type_classification=type_classification,
            type_lens=type_lens,
        ),
        verdict=aggregation.overallVerdictDraft,
        verdictSubQuote=aggregation.verdictSubQuote,
        summary=aggregation.overallSummaryDraft,
        platformCandidates=aggregation.platformCandidates,
        marketFit=aggregation.marketFitDraft,
        strengths=aggregation.strengthCandidates,
        weaknesses=aggregation.weaknessCandidates,
    )
    type_assessment = TypeAssessmentResult(
        novelType=type_classification.novelType,
        classificationConfidence=type_classification.classificationConfidence,
        fallbackUsed=type_classification.fallbackUsed,
        summary=type_lens.summary,
        lenses=list(type_lens.items),
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
        typeAssessment=type_assessment,
    )


def _build_overall_score(
    *,
    axes: list[AxisEvaluationResult],
    rubric: RubricEvaluationSet,
    consistency: ConsistencyCheckResult,
    type_classification: TypeClassificationResult,
    type_lens: TypeLensEvaluationResult,
) -> int:
    universal_base = round(sum(axis.score for axis in axes) / len(axes))
    lens_scores = [_SCORE_BAND_TO_SCORE[item.scoreBand] for item in type_lens.items]
    lens_base = round(sum(lens_scores) / len(lens_scores))
    type_weight = 0.15 if type_classification.novelType is NovelType.GENERAL_FALLBACK else 0.25
    base_score = round(universal_base * (1 - type_weight) + lens_base * type_weight)
    if rubric.evaluationMode is EvaluationMode.DEGRADED:
        base_score -= 8
    if consistency.duplicatedPenaltiesDetected:
        base_score -= 3
    if any(conflict.conflictType is ConflictType.WEAK_EVIDENCE for conflict in consistency.conflicts):
        base_score -= 4
    return max(0, min(100, base_score))
