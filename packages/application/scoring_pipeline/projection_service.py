from __future__ import annotations

from packages.schemas.common.enums import TopLevelScoreField
from packages.schemas.output.result import FinalEvaluationProjection, PlatformRecommendation
from packages.schemas.stages.aggregation import AggregatedRubricResult


def build_final_projection(*, aggregation: AggregatedRubricResult) -> FinalEvaluationProjection:
    platform_score = aggregation.topLevelScoresDraft[TopLevelScoreField.COMMERCIAL_VALUE]
    detailed = aggregation.detailedAnalysisDraft
    platforms = []
    if aggregation.platformCandidates:
        primary_platform = aggregation.platformCandidates[0]
        platforms = [
            PlatformRecommendation(
                name=primary_platform,
                percentage=platform_score,
                reason=aggregation.marketFitDraft,
            )
        ]
    return FinalEvaluationProjection(
        taskId=aggregation.taskId,
        schemaVersion=aggregation.schemaVersion,
        promptVersion=aggregation.promptVersion,
        rubricVersion=aggregation.rubricVersion,
        providerId=aggregation.providerId,
        modelId=aggregation.modelId,
        signingProbability=aggregation.topLevelScoresDraft[TopLevelScoreField.SIGNING_PROBABILITY],
        commercialValue=aggregation.topLevelScoresDraft[TopLevelScoreField.COMMERCIAL_VALUE],
        writingQuality=aggregation.topLevelScoresDraft[TopLevelScoreField.WRITING_QUALITY],
        innovationScore=aggregation.topLevelScoresDraft[TopLevelScoreField.INNOVATION_SCORE],
        strengths=aggregation.strengthCandidates,
        weaknesses=aggregation.weaknessCandidates,
        platforms=platforms,
        marketFit=aggregation.marketFitDraft,
        editorVerdict=aggregation.editorVerdictDraft,
        detailedAnalysis=detailed,
        overallConfidence=aggregation.overallConfidence,
        supportingAxisMap=aggregation.supportingAxisMap,
        supportingSkeletonMap=aggregation.supportingSkeletonMap,
    )
