from __future__ import annotations

from packages.schemas.common.enums import TopLevelScoreField
from packages.schemas.output.result import DetailedAnalysis, FinalEvaluationProjection, PlatformRecommendation
from packages.schemas.stages.aggregation import AggregatedRubricResult


def build_final_projection(*, aggregation: AggregatedRubricResult) -> FinalEvaluationProjection:
    platform_name = aggregation.platformCandidates[0] if aggregation.platformCandidates else "通用网文平台"
    platform_score = aggregation.topLevelScoresDraft.get(TopLevelScoreField.COMMERCIAL_VALUE, 60)
    detailed = aggregation.detailedAnalysisDraft
    if not isinstance(detailed, DetailedAnalysis):
        detailed = DetailedAnalysis(
            plot="情节结构已形成基础闭环。",
            character="角色驱动存在进一步强化空间。",
            pacing="节奏整体稳定。",
            worldBuilding="设定基础明确。",
        )
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
        platforms=[
            PlatformRecommendation(
                name=platform_name,
                percentage=platform_score,
                reason="平台候选由 aggregation 草案映射得出。",
            )
        ],
        marketFit=aggregation.marketFitDraft,
        editorVerdict=aggregation.editorVerdictDraft,
        detailedAnalysis=detailed,
        overallConfidence=aggregation.overallConfidence,
        supportingAxisMap=aggregation.supportingAxisMap,
        supportingSkeletonMap=aggregation.supportingSkeletonMap,
    )
