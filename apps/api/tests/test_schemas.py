from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.schemas.common.base import MetaData
from packages.schemas.common.enums import (
    AxisId,
    EvaluationMode,
    FatalRisk,
    InputComposition,
    ResultStatus,
    ScoreBand,
    SkeletonDimensionId,
    StageName,
    StageStatus,
    SubmissionSourceType,
    Sufficiency,
    TaskStatus,
    TopLevelScoreField,
)
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline
from packages.schemas.input.screening import InputScreeningResult
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.dashboard import DashboardSummary, HistoryList
from packages.schemas.output.result import (
    DetailedAnalysis,
    EvaluationResult,
    EvaluationResultResource,
    FinalEvaluationProjection,
    PlatformRecommendation,
)
from packages.schemas.output.task import EvaluationTask, EvaluationTaskSummary, RecentResultSummary
from packages.schemas.stages.aggregation import AggregatedRubricResult
from packages.schemas.stages.rubric import RubricEvaluationEvidenceRef, RubricEvaluationItem, RubricEvaluationSet


def build_result() -> EvaluationResult:
    return EvaluationResult(
        taskId="task_1",
        schemaVersion="1.0.0",
        promptVersion="prompt-v1",
        rubricVersion="rubric-v1",
        providerId="provider-local",
        modelId="model-local",
        resultTime="2026-03-25T00:00:00Z",
        signingProbability=80,
        commercialValue=78,
        writingQuality=76,
        innovationScore=74,
        strengths=["人物动机清晰"],
        weaknesses=["开篇冲突偏慢"],
        platforms=[
            PlatformRecommendation(
                name="女频平台 A",
                percentage=82,
                reason="题材匹配度较高",
            )
        ],
        marketFit="具备一定市场接受度",
        editorVerdict="可继续观察",
        detailedAnalysis=DetailedAnalysis(
            plot="情节推进稳定",
            character="角色动机明确",
            pacing="节奏略慢",
            worldBuilding="设定表达完整",
        ),
    )


def build_rubric_item(axis_id: AxisId) -> RubricEvaluationItem:
    return RubricEvaluationItem(
        evaluationId=f"eval-{axis_id.value}",
        axisId=axis_id,
        scoreBand=ScoreBand.THREE,
        reason="证据充分，表现合格。",
        evidenceRefs=[
            RubricEvaluationEvidenceRef(
                sourceType="chapters",
                sourceSpan={"chapterIndex": 0},
                excerpt="示例片段",
                observationType="narrative_observation",
                evidenceNote="用于说明判断依据",
                confidence=0.8,
            )
        ],
        confidence=0.8,
        riskTags=[],
        blockingSignals=[],
        affectedSkeletonDimensions=[],
        degradedByInput=False,
    )


def test_joint_submission_request_derives_input_shape() -> None:
    request = JointSubmissionRequest(
        title="测试稿件",
        chapters=[ManuscriptChapter(content="第一章内容", title="第一章")],
        outline=ManuscriptOutline(content="大纲内容"),
        sourceType=SubmissionSourceType.DIRECT_INPUT,
    )

    assert request.hasChapters is True
    assert request.hasOutline is True
    assert request.inputComposition is InputComposition.CHAPTERS_OUTLINE


def test_joint_submission_request_rejects_empty_submission() -> None:
    with pytest.raises(ValidationError):
        JointSubmissionRequest(
            title="空输入",
            chapters=[],
            outline=None,
            sourceType=SubmissionSourceType.DIRECT_INPUT,
        )


def test_evaluation_task_rejects_invalid_status_combination() -> None:
    with pytest.raises(ValidationError):
        EvaluationTask(
            taskId="task_1",
            title="测试稿件",
            inputSummary="已提交 1 章正文和 1 份大纲",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            hasChapters=True,
            hasOutline=True,
            evaluationMode=EvaluationMode.FULL,
            status=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.NOT_AVAILABLE,
            createdAt="2026-03-25T00:00:00Z",
            updatedAt="2026-03-25T00:00:00Z",
        )


def test_evaluation_task_requires_error_for_blocked_state() -> None:
    with pytest.raises(ValidationError):
        EvaluationTask(
            taskId="task_1",
            title="测试稿件",
            inputSummary="仅提交大纲",
            inputComposition=InputComposition.OUTLINE_ONLY,
            hasChapters=False,
            hasOutline=True,
            evaluationMode=EvaluationMode.DEGRADED,
            status=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.BLOCKED,
            createdAt="2026-03-25T00:00:00Z",
            updatedAt="2026-03-25T00:00:00Z",
        )


def test_input_screening_result_enforces_full_mode_requirements() -> None:
    with pytest.raises(ValidationError):
        InputScreeningResult(
            taskId="task_1",
            stage=StageName.INPUT_SCREENING,
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            inputComposition=InputComposition.OUTLINE_ONLY,
            hasChapters=False,
            hasOutline=True,
            chaptersSufficiency=Sufficiency.MISSING,
            outlineSufficiency=Sufficiency.SUFFICIENT,
            evaluationMode=EvaluationMode.FULL,
            rateable=True,
            status=StageStatus.OK,
            rejectionReasons=[],
            riskTags=[],
            segmentationPlan=None,
            confidence=0.9,
            continueAllowed=True,
        )


def test_input_screening_result_accepts_fatal_risk_tags() -> None:
    result = InputScreeningResult(
        taskId="task_1",
        stage=StageName.INPUT_SCREENING,
        schemaVersion="1.0.0",
        promptVersion="prompt-v1",
        rubricVersion="rubric-v1",
        providerId="provider-local",
        modelId="model-local",
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        hasChapters=True,
        hasOutline=True,
        chaptersSufficiency=Sufficiency.SUFFICIENT,
        outlineSufficiency=Sufficiency.SUFFICIENT,
        evaluationMode=EvaluationMode.FULL,
        rateable=True,
        status=StageStatus.OK,
        rejectionReasons=[],
        riskTags=[FatalRisk.AI_MANUAL_TONE],
        segmentationPlan=None,
        confidence=0.9,
        continueAllowed=True,
    )

    assert result.riskTags == [FatalRisk.AI_MANUAL_TONE]


def test_input_screening_result_rejects_unknown_risk_tag() -> None:
    with pytest.raises(ValidationError):
        InputScreeningResult(
            taskId="task_1",
            stage=StageName.INPUT_SCREENING,
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            hasChapters=True,
            hasOutline=True,
            chaptersSufficiency=Sufficiency.SUFFICIENT,
            outlineSufficiency=Sufficiency.SUFFICIENT,
            evaluationMode=EvaluationMode.FULL,
            rateable=True,
            status=StageStatus.OK,
            rejectionReasons=[],
            riskTags=["unknown_risk_tag"],
            segmentationPlan=None,
            confidence=0.9,
            continueAllowed=True,
        )


def test_rubric_evaluation_set_requires_all_axes_in_full_mode() -> None:
    with pytest.raises(ValidationError):
        RubricEvaluationSet(
            taskId="task_1",
            stage=StageName.RUBRIC_EVALUATION,
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            evaluationMode=EvaluationMode.FULL,
            items=[build_rubric_item(AxisId.HOOK_RETENTION)],
            axisSummaries={AxisId.HOOK_RETENTION: "开篇抓力合格"},
            missingRequiredAxes=[AxisId.SERIAL_MOMENTUM],
            riskTags=[],
            overallConfidence=0.8,
        )


def test_evaluation_task_rejects_wrong_error_code_category() -> None:
    with pytest.raises(ValidationError):
        EvaluationTask(
            taskId="task_1",
            title="测试稿件",
            inputSummary="仅提交大纲",
            inputComposition=InputComposition.OUTLINE_ONLY,
            hasChapters=False,
            hasOutline=True,
            evaluationMode=EvaluationMode.DEGRADED,
            status=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.BLOCKED,
            errorCode=ErrorCode.INTERNAL_ERROR,
            errorMessage="错误分类不匹配",
            createdAt="2026-03-25T00:00:00Z",
            updatedAt="2026-03-25T00:00:00Z",
        )


def test_evaluation_result_resource_requires_result_when_available() -> None:
    with pytest.raises(ValidationError):
        EvaluationResultResource(
            taskId="task_1",
            resultStatus=ResultStatus.AVAILABLE,
            resultTime="2026-03-25T00:00:00Z",
            result=None,
            message=None,
        )


def test_evaluation_result_resource_requires_message_when_blocked() -> None:
    with pytest.raises(ValidationError):
        EvaluationResultResource(
            taskId="task_1",
            resultStatus=ResultStatus.BLOCKED,
            resultTime=None,
            result=None,
            message=None,
        )


def test_evaluation_result_resource_accepts_available_result() -> None:
    resource = EvaluationResultResource(
        taskId="task_1",
        resultStatus=ResultStatus.AVAILABLE,
        resultTime="2026-03-25T00:00:00Z",
        result=build_result(),
        message=None,
    )

    assert resource.result is not None
    assert resource.resultStatus is ResultStatus.AVAILABLE
    assert resource.result.signingProbability == 80
    assert ErrorCode.RESULT_NOT_AVAILABLE.value == "RESULT_NOT_AVAILABLE"


def test_rubric_evaluation_set_requires_complete_axis_summaries() -> None:
    items = [build_rubric_item(axis_id) for axis_id in AxisId]
    with pytest.raises(ValidationError):
        RubricEvaluationSet(
            taskId="task_1",
            stage=StageName.RUBRIC_EVALUATION,
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            evaluationMode=EvaluationMode.FULL,
            items=items,
            axisSummaries={AxisId.HOOK_RETENTION: "仅覆盖一个轴"},
            missingRequiredAxes=[],
            riskTags=[FatalRisk.STALE_FORMULA],
            overallConfidence=0.8,
        )


def test_final_projection_requires_all_supporting_maps() -> None:
    with pytest.raises(ValidationError):
        FinalEvaluationProjection(
            taskId="task_1",
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            signingProbability=80,
            commercialValue=78,
            writingQuality=76,
            innovationScore=74,
            strengths=["人物动机清晰"],
            weaknesses=["开篇冲突偏慢"],
            platforms=[
                PlatformRecommendation(name="女频平台 A", percentage=82, reason="题材匹配度较高")
            ],
            marketFit="具备一定市场接受度",
            editorVerdict="可继续观察",
            detailedAnalysis=DetailedAnalysis(
                plot="情节推进稳定",
                character="角色动机明确",
                pacing="节奏略慢",
                worldBuilding="设定表达完整",
            ),
            overallConfidence=0.8,
            supportingAxisMap={TopLevelScoreField.SIGNING_PROBABILITY: [AxisId.PLATFORM_FIT]},
            supportingSkeletonMap={TopLevelScoreField.SIGNING_PROBABILITY: [SkeletonDimensionId.MARKET_ATTRACTION]},
        )


def test_dashboard_and_history_summary_accept_valid_payload() -> None:
    summary = EvaluationTaskSummary(
        taskId="task_1",
        title="测试稿件",
        inputSummary="已提交 1 章正文和 1 份大纲",
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        status=TaskStatus.PROCESSING,
        resultStatus=ResultStatus.NOT_AVAILABLE,
        createdAt="2026-03-25T00:00:00Z",
    )
    recent_result = RecentResultSummary(
        taskId="task_2",
        title="另一篇测试稿",
        resultTime="2026-03-25T01:00:00Z",
        signingProbability=84,
        editorVerdict="有签约潜力",
    )

    dashboard = DashboardSummary(
        recentTasks=[summary],
        activeTasks=[summary],
        recentResults=[recent_result],
    )
    history = HistoryList(
        items=[summary],
        meta=MetaData(nextCursor=None, limit=20),
    )

    assert dashboard.recentTasks[0].taskId == "task_1"
    assert history.meta.limit == 20


def build_aggregated_rubric_result() -> AggregatedRubricResult:
    return AggregatedRubricResult(
        taskId="task_1",
        schemaVersion="1.0.0",
        promptVersion="prompt-v1",
        rubricVersion="rubric-v1",
        providerId="provider-local",
        modelId="model-local",
        axisScores={axis_id: 80 for axis_id in AxisId},
        skeletonScores={dimension_id: 78 for dimension_id in SkeletonDimensionId},
        topLevelScoresDraft={score_field: 76 for score_field in TopLevelScoreField},
        strengthCandidates=["题材明确"],
        weaknessCandidates=["冲突偏弱"],
        platformCandidates=["女频平台 A"],
        marketFitDraft="具备一定市场接受度",
        editorVerdictDraft="可继续观察",
        detailedAnalysisDraft=DetailedAnalysis(
            plot="情节推进稳定",
            character="角色动机明确",
            pacing="节奏略慢",
            worldBuilding="设定表达完整",
        ),
        supportingAxisMap={score_field: [AxisId.PLATFORM_FIT] for score_field in TopLevelScoreField},
        supportingSkeletonMap={
            score_field: [SkeletonDimensionId.MARKET_ATTRACTION] for score_field in TopLevelScoreField
        },
        riskTags=[FatalRisk.STALE_FORMULA],
        overallConfidence=0.8,
    )


def test_aggregated_rubric_result_accepts_complete_valid_payload() -> None:
    result = build_aggregated_rubric_result()

    assert result.platformCandidates == ["女频平台 A"]
    assert result.topLevelScoresDraft[TopLevelScoreField.SIGNING_PROBABILITY] == 76


def test_aggregated_rubric_result_requires_full_fixed_maps() -> None:
    payload = build_aggregated_rubric_result().model_dump(mode="json")
    payload.update(
        {
            "axisScores": {AxisId.HOOK_RETENTION.value: 80},
            "skeletonScores": {SkeletonDimensionId.MARKET_ATTRACTION.value: 80},
            "topLevelScoresDraft": {TopLevelScoreField.SIGNING_PROBABILITY.value: 80},
            "supportingAxisMap": {TopLevelScoreField.SIGNING_PROBABILITY.value: [AxisId.PLATFORM_FIT.value]},
            "supportingSkeletonMap": {
                TopLevelScoreField.SIGNING_PROBABILITY.value: [SkeletonDimensionId.MARKET_ATTRACTION.value]
            },
        }
    )

    with pytest.raises(ValidationError):
        AggregatedRubricResult.model_validate(payload)
