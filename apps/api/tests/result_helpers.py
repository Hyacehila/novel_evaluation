from __future__ import annotations

from packages.schemas.common.enums import AxisId, ScoreBand
from packages.schemas.output.result import AxisEvaluationResult, FinalEvaluationProjection, OverallEvaluationResult
from packages.schemas.output.task import EvaluationTask
from packages.schemas.stages.aggregation import PlatformCandidate


def build_projection(
    task: EvaluationTask,
    *,
    score: int = 80,
    schema_version: str | None = None,
    prompt_version: str | None = None,
    rubric_version: str | None = None,
    provider_id: str | None = None,
    model_id: str | None = None,
) -> FinalEvaluationProjection:
    return FinalEvaluationProjection(
        taskId=task.taskId,
        schemaVersion=schema_version or task.schemaVersion or "schema-test-v1",
        promptVersion=prompt_version or task.promptVersion or "prompt-test-v1",
        rubricVersion=rubric_version or task.rubricVersion or "rubric-test-v1",
        providerId=provider_id or task.providerId or "provider-test",
        modelId=model_id or task.modelId or "model-test",
        axes=[
            AxisEvaluationResult(
                axisId=axis_id,
                scoreBand=ScoreBand.THREE,
                score=score,
                summary=f"{axis_id.value} 维度总结",
                reason=f"{axis_id.value} 维度理由",
                degradedByInput=False,
                riskTags=[],
            )
            for axis_id in AxisId
        ],
        overall=OverallEvaluationResult(
            score=score,
            verdict="可继续观察",
            verdictSubQuote="当前样本已体现基础市场承接力，但仍需观察长线兑现稳定性。",
            summary="整体完成度稳定，仍需观察兑现强度。",
            platformCandidates=[
                PlatformCandidate(
                    name="女频平台 A",
                    weight=100,
                    pitchQuote="情感走向与平台核心读者预期一致，具备明确承接空间。",
                )
            ],
            marketFit="具备一定市场接受度",
            strengths=["结构完成度稳定"],
            weaknesses=["长线兑现仍需继续观察"],
        ),
    )
