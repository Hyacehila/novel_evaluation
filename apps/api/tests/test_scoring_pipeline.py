from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest

from packages.application.scoring_pipeline.consistency_service import run_consistency_check
from packages.application.scoring_pipeline.exceptions import PipelineBlockedError, PipelineFailureError
from packages.application.scoring_pipeline.aggregation_executor import execute_aggregation
from packages.application.scoring_pipeline.models import (
    AggregationExecutionContext,
    RubricExecutionContext,
    ScreeningExecutionContext,
    StagePromptBinding,
)
from packages.application.scoring_pipeline.orchestration import ScoringPipeline
from packages.application.scoring_pipeline.projection_service import build_final_projection
from packages.application.scoring_pipeline.rubric_executor import execute_rubric
from packages.application.scoring_pipeline.screening_executor import execute_screening
from packages.schemas.common.enums import (
    AxisId,
    EvaluationMode,
    EvidenceSourceType,
    FatalRisk,
    InputComposition,
    ResultStatus,
    ScoreBand,
    SkeletonDimensionId,
    StageName,
    StageStatus,
    Sufficiency,
    TaskStatus,
    TopLevelScoreField,
)
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline
from packages.schemas.input.screening import InputScreeningResult
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.result import DetailedAnalysis
from packages.schemas.output.task import EvaluationTask
from packages.schemas.stages.aggregation import AggregatedRubricResult
from packages.schemas.stages.consistency import ConflictType
from packages.schemas.stages.rubric import RubricEvaluationEvidenceRef, RubricEvaluationItem, RubricEvaluationSet


@dataclass(frozen=True, slots=True)
class StubResolvedPrompt:
    promptId: str = "prompt-test"
    promptVersion: str = "prompt-test-v1"
    schemaVersion: str = "schema-test-v1"
    rubricVersion: str = "rubric-test-v1"
    body: str = "你是测试用提示词。"


@dataclass(frozen=True, slots=True)
class StubProviderSuccess:
    rawJson: Any
    rawText: str = "{}"


@dataclass(slots=True)
class RecordingPromptRuntime:
    resolved_prompt: StubResolvedPrompt = field(default_factory=StubResolvedPrompt)
    calls: list[dict[str, str]] = field(default_factory=list)

    def resolve(
        self,
        *,
        stage: str,
        input_composition: str,
        evaluation_mode: str,
        provider_id: str,
        model_id: str,
    ) -> StubResolvedPrompt:
        self.calls.append(
            {
                "stage": stage,
                "input_composition": input_composition,
                "evaluation_mode": evaluation_mode,
                "provider_id": provider_id,
                "model_id": model_id,
            }
        )
        return self.resolved_prompt


@dataclass(slots=True)
class RecordingProviderAdapter:
    payloads: dict[StageName, Any]
    provider_id: str = "provider-test"
    model_id: str = "model-test"
    requests: list[Any] = field(default_factory=list)

    def execute(self, request: Any) -> StubProviderSuccess:
        self.requests.append(request)
        payload = self.payloads[request.stage]
        if callable(payload):
            payload = payload(request)
        return StubProviderSuccess(rawJson=payload)


def build_submission(
    *,
    chapter_text: str = "都市职场开篇直接抛出悬念与冲突，主角决定反击。",
    outline_text: str = "都市豪门主线明确，后续阶段目标稳定推进。",
    with_chapters: bool = True,
    with_outline: bool = True,
) -> JointSubmissionRequest:
    return JointSubmissionRequest(
        title="测试稿件",
        chapters=[ManuscriptChapter(title="第一章", content=chapter_text)] if with_chapters else None,
        outline=ManuscriptOutline(content=outline_text) if with_outline else None,
        sourceType="direct_input",
    )


def build_stage_binding(*, stage: StageName = StageName.RUBRIC_EVALUATION) -> StagePromptBinding:
    return StagePromptBinding(
        stage=stage,
        prompt_id=f"{stage.value}-prompt",
        prompt_version="prompt-test-v1",
        schema_version="schema-test-v1",
        rubric_version="rubric-test-v1",
        provider_id="provider-test",
        model_id="model-test",
        prompt_body="你是测试用提示词。",
    )


def build_screening_result(
    *,
    input_composition: InputComposition = InputComposition.CHAPTERS_OUTLINE,
    evaluation_mode: EvaluationMode = EvaluationMode.FULL,
    has_chapters: bool = True,
    has_outline: bool = True,
    chapters_sufficiency: Sufficiency = Sufficiency.SUFFICIENT,
    outline_sufficiency: Sufficiency = Sufficiency.SUFFICIENT,
    continue_allowed: bool = True,
    rateable: bool = True,
    rejection_reasons: list[str] | None = None,
) -> InputScreeningResult:
    return InputScreeningResult(
        taskId="task_pipeline_001",
        schemaVersion="schema-test-v1",
        promptVersion="prompt-test-v1",
        rubricVersion="rubric-test-v1",
        providerId="provider-test",
        modelId="model-test",
        inputComposition=input_composition,
        hasChapters=has_chapters,
        hasOutline=has_outline,
        chaptersSufficiency=chapters_sufficiency,
        outlineSufficiency=outline_sufficiency,
        evaluationMode=evaluation_mode,
        rateable=rateable,
        status=StageStatus.OK if continue_allowed else StageStatus.UNRATEABLE,
        rejectionReasons=rejection_reasons or ([] if continue_allowed else ["输入材料不足，无法形成稳定评分结论。"]),
        riskTags=[] if continue_allowed else [FatalRisk.INSUFFICIENT_MATERIAL],
        segmentationPlan=None,
        confidence=0.9 if continue_allowed else 0.24,
        continueAllowed=continue_allowed,
    )


def build_evidence(
    *,
    source_type: EvidenceSourceType = EvidenceSourceType.CHAPTERS,
    excerpt: str = "示例片段展示了冲突与行动目标。",
    confidence: float = 0.8,
) -> RubricEvaluationEvidenceRef:
    return RubricEvaluationEvidenceRef(
        sourceType=source_type,
        sourceSpan={"chapterIndex": 0},
        excerpt=excerpt,
        observationType="narrative_observation",
        evidenceNote="用于说明判断依据",
        confidence=confidence,
    )


def build_rubric_item(
    axis_id: AxisId,
    *,
    evaluation_id: str | None = None,
    reason: str = "证据充分，表现稳定。",
    confidence: float = 0.8,
    evidence_confidence: float = 0.8,
    source_type: EvidenceSourceType = EvidenceSourceType.CHAPTERS,
    excerpt: str = "示例片段展示了冲突与行动目标。",
    evidence_refs: list[RubricEvaluationEvidenceRef] | None = None,
    risk_tags: list[FatalRisk] | None = None,
    blocking_signals: list[str] | None = None,
) -> RubricEvaluationItem:
    return RubricEvaluationItem(
        evaluationId=evaluation_id or f"eval-{axis_id.value}",
        axisId=axis_id,
        scoreBand=ScoreBand.THREE,
        reason=reason,
        evidenceRefs=evidence_refs
        or [build_evidence(source_type=source_type, excerpt=excerpt, confidence=evidence_confidence)],
        confidence=confidence,
        riskTags=risk_tags or [],
        blockingSignals=blocking_signals or [],
        affectedSkeletonDimensions=[SkeletonDimensionId.MARKET_ATTRACTION],
        degradedByInput=False,
    )


def build_rubric_set(
    *,
    input_composition: InputComposition = InputComposition.CHAPTERS_OUTLINE,
    evaluation_mode: EvaluationMode = EvaluationMode.FULL,
    item_overrides: dict[AxisId, RubricEvaluationItem] | None = None,
    missing_required_axes: list[AxisId] | None = None,
    overall_confidence: float = 0.8,
) -> RubricEvaluationSet:
    overrides = item_overrides or {}
    items = [overrides.get(axis_id, build_rubric_item(axis_id)) for axis_id in AxisId]
    return RubricEvaluationSet(
        taskId="task_pipeline_001",
        schemaVersion="schema-test-v1",
        promptVersion="prompt-test-v1",
        rubricVersion="rubric-test-v1",
        providerId="provider-test",
        modelId="model-test",
        inputComposition=input_composition,
        evaluationMode=evaluation_mode,
        items=items,
        axisSummaries={axis_id: f"{axis_id.value} 维度总结" for axis_id in AxisId},
        missingRequiredAxes=missing_required_axes or [],
        riskTags=[],
        overallConfidence=overall_confidence,
    )


def build_aggregation_result(
    *,
    platform_candidates: list[str] | None = None,
    market_fit: str = "当前题材更贴合女频平台 A 的用户预期。",
    commercial_value: int = 78,
) -> AggregatedRubricResult:
    return AggregatedRubricResult(
        taskId="task_pipeline_001",
        schemaVersion="schema-test-v1",
        promptVersion="prompt-test-v1",
        rubricVersion="rubric-test-v1",
        providerId="provider-test",
        modelId="model-test",
        axisScores={axis_id: 76 for axis_id in AxisId},
        skeletonScores={dimension_id: 74 for dimension_id in SkeletonDimensionId},
        topLevelScoresDraft={
            TopLevelScoreField.SIGNING_PROBABILITY: 80,
            TopLevelScoreField.COMMERCIAL_VALUE: commercial_value,
            TopLevelScoreField.WRITING_QUALITY: 76,
            TopLevelScoreField.INNOVATION_SCORE: 74,
        },
        strengthCandidates=["题材抓手明确"],
        weaknessCandidates=["兑现节奏仍可补强"],
        platformCandidates=platform_candidates if platform_candidates is not None else ["女频平台 A", "女频平台 B"],
        marketFitDraft=market_fit,
        editorVerdictDraft="建议继续观察并进入样章复核。",
        detailedAnalysisDraft=DetailedAnalysis(
            plot="情节推进稳定。",
            character="角色动机明确。",
            pacing="节奏略慢但可读。",
            worldBuilding="设定卖点清晰。",
        ),
        supportingAxisMap={
            TopLevelScoreField.SIGNING_PROBABILITY: [AxisId.PLATFORM_FIT, AxisId.COMMERCIAL_POTENTIAL],
            TopLevelScoreField.COMMERCIAL_VALUE: [AxisId.COMMERCIAL_POTENTIAL, AxisId.SERIAL_MOMENTUM],
            TopLevelScoreField.WRITING_QUALITY: [AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF],
            TopLevelScoreField.INNOVATION_SCORE: [AxisId.SETTING_DIFFERENTIATION, AxisId.HOOK_RETENTION],
        },
        supportingSkeletonMap={
            TopLevelScoreField.SIGNING_PROBABILITY: [SkeletonDimensionId.MARKET_ATTRACTION],
            TopLevelScoreField.COMMERCIAL_VALUE: [
                SkeletonDimensionId.MARKET_ATTRACTION,
                SkeletonDimensionId.CHARACTER_MOMENTUM,
            ],
            TopLevelScoreField.WRITING_QUALITY: [SkeletonDimensionId.NARRATIVE_EXECUTION],
            TopLevelScoreField.INNOVATION_SCORE: [SkeletonDimensionId.NOVELTY_UTILITY],
        },
        riskTags=[],
        overallConfidence=0.82,
    )


def build_task(
    *,
    evaluation_mode: EvaluationMode = EvaluationMode.FULL,
    input_composition: InputComposition = InputComposition.CHAPTERS_OUTLINE,
) -> EvaluationTask:
    now = datetime(2026, 3, 27, tzinfo=timezone.utc)
    return EvaluationTask(
        taskId="task_pipeline_001",
        title="测试稿件",
        inputSummary="已提交 1 章正文和 1 份大纲",
        inputComposition=input_composition,
        hasChapters=input_composition is not InputComposition.OUTLINE_ONLY,
        hasOutline=input_composition is not InputComposition.CHAPTERS_ONLY,
        evaluationMode=evaluation_mode,
        status=TaskStatus.PROCESSING,
        resultStatus=ResultStatus.NOT_AVAILABLE,
        createdAt=now,
        startedAt=now,
        updatedAt=now,
    )


def build_rubric_context(
    *,
    submission: JointSubmissionRequest | None = None,
    screening: InputScreeningResult | None = None,
) -> RubricExecutionContext:
    return RubricExecutionContext(
        task_id="task_pipeline_001",
        submission=submission or build_submission(),
        screening=screening or build_screening_result(),
        binding=build_stage_binding(stage=StageName.RUBRIC_EVALUATION),
    )


def build_aggregation_context(
    *,
    submission: JointSubmissionRequest | None = None,
    screening: InputScreeningResult | None = None,
    rubric: RubricEvaluationSet | None = None,
) -> AggregationExecutionContext:
    resolved_submission = submission or build_submission()
    resolved_screening = screening or build_screening_result()
    resolved_rubric = rubric or build_rubric_set(
        input_composition=resolved_screening.inputComposition,
        evaluation_mode=resolved_screening.evaluationMode,
    )
    rubric_context = build_rubric_context(submission=resolved_submission, screening=resolved_screening)
    consistency = run_consistency_check(context=rubric_context, rubric=resolved_rubric)
    return AggregationExecutionContext(
        task_id="task_pipeline_001",
        submission=resolved_submission,
        screening=resolved_screening,
        rubric=resolved_rubric,
        consistency=consistency,
        binding=build_stage_binding(stage=StageName.AGGREGATION),
    )


def build_screening_context(
    *,
    submission: JointSubmissionRequest | None = None,
    evaluation_mode_hint: EvaluationMode = EvaluationMode.FULL,
) -> ScreeningExecutionContext:
    resolved_submission = submission or build_submission()
    return ScreeningExecutionContext(
        task_id="task_pipeline_001",
        submission=resolved_submission,
        input_composition=resolved_submission.inputComposition.value,
        evaluation_mode_hint=evaluation_mode_hint,
        binding=build_stage_binding(stage=StageName.INPUT_SCREENING),
    )


def test_execute_screening_normalizes_joint_input_full_mode_and_metadata() -> None:
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: {
                "taskId": "task-from-model",
                "stage": "input_screening",
                "schemaVersion": "1.0",
                "promptVersion": "1.0",
                "rubricVersion": "1.0",
                "providerId": "default",
                "modelId": "default",
                "inputComposition": "outline_only",
                "hasChapters": False,
                "hasOutline": True,
                "chaptersSufficiency": "sufficient",
                "outlineSufficiency": "sufficient",
                "evaluationMode": "degraded",
                "rateable": True,
                "status": "warning",
                "rejectionReasons": [],
                "riskTags": ["aiManualTone", "unknownRisk"],
                "confidence": 0.9,
                "continueAllowed": True,
            }
        }
    )

    result = execute_screening(provider_adapter=provider, context=build_screening_context())

    assert result.taskId == "task_pipeline_001"
    assert result.schemaVersion == "schema-test-v1"
    assert result.promptVersion == "prompt-test-v1"
    assert result.rubricVersion == "rubric-test-v1"
    assert result.providerId == "provider-test"
    assert result.modelId == "model-test"
    assert result.inputComposition is InputComposition.CHAPTERS_OUTLINE
    assert result.hasChapters is True
    assert result.hasOutline is True
    assert result.evaluationMode is EvaluationMode.FULL
    assert result.riskTags == [FatalRisk.AI_MANUAL_TONE]


def test_execute_screening_fail_fast_blocks_low_confidence_non_narrative_joint_input() -> None:
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: {
                "taskId": "task-from-model",
                "stage": "input_screening",
                "schemaVersion": "1.0",
                "promptVersion": "1.0",
                "rubricVersion": "1.0",
                "providerId": "default",
                "modelId": "default",
                "inputComposition": "chapters_outline",
                "hasChapters": True,
                "hasOutline": True,
                "chaptersSufficiency": "insufficient",
                "outlineSufficiency": "insufficient",
                "evaluationMode": "degraded",
                "rateable": True,
                "status": "warning",
                "rejectionReasons": [],
                "riskTags": ["nonNarrativeSubmission", "insufficientMaterial"],
                "confidence": 0.3,
                "continueAllowed": True,
            }
        }
    )
    submission = build_submission(
        chapter_text="剧情梗概：人物出场、冲突升级、结局兑现。",
        outline_text="大纲摘要：前期铺垫，中期升级，后期收束。",
    )

    result = execute_screening(provider_adapter=provider, context=build_screening_context(submission=submission))

    assert result.evaluationMode is EvaluationMode.DEGRADED
    assert result.rateable is False
    assert result.continueAllowed is False
    assert result.status is StageStatus.UNRATEABLE
    assert result.rejectionReasons[0].startswith("正文与大纲仍停留在梗概")


def test_execute_rubric_normalizes_real_deepseek_schema_drift() -> None:
    alias_by_axis = {
        AxisId.HOOK_RETENTION: "conflict",
        AxisId.SERIAL_MOMENTUM: "progression",
        AxisId.CHARACTER_DRIVE: "protagonist",
        AxisId.NARRATIVE_CONTROL: "clarity",
        AxisId.PACING_PAYOFF: "pacing",
        AxisId.SETTING_DIFFERENTIATION: "originality",
        AxisId.PLATFORM_FIT: "genre_conventions",
        AxisId.COMMERCIAL_POTENTIAL: "longevity",
    }
    source_type_by_axis = {
        AxisId.HOOK_RETENTION: "chapters",
        AxisId.SERIAL_MOMENTUM: "chapters",
        AxisId.CHARACTER_DRIVE: "chapters",
        AxisId.NARRATIVE_CONTROL: "outline",
        AxisId.PACING_PAYOFF: "outline",
        AxisId.SETTING_DIFFERENTIATION: "cross_input",
        AxisId.PLATFORM_FIT: "cross_input",
        AxisId.COMMERCIAL_POTENTIAL: "chapters",
    }
    source_span_by_axis = {
        AxisId.HOOK_RETENTION: "第一章",
        AxisId.SERIAL_MOMENTUM: "第二章",
        AxisId.CHARACTER_DRIVE: "第三章",
        AxisId.NARRATIVE_CONTROL: "全段",
        AxisId.PACING_PAYOFF: "尾段",
        AxisId.SETTING_DIFFERENTIATION: "chapters: 第一章; outline: 全段",
        AxisId.PLATFORM_FIT: "chapters: 第二章; outline: 题材定位",
        AxisId.COMMERCIAL_POTENTIAL: "终章",
    }
    raw_payload = {
        "taskId": "task-from-model",
        "stage": "rubric_evaluation",
        "schemaVersion": "1.0",
        "promptVersion": "1.0",
        "rubricVersion": "1.0",
        "providerId": "default",
        "modelId": "default",
        "inputComposition": "chapters_outline",
        "evaluationMode": "full",
        "items": [
            {
                "evaluationId": f"model-{axis_id.value}",
                "axisId": axis_id.value,
                "scoreBand": "3",
                "reason": f"{axis_id.value} 的判断依据完整。",
                "evidenceRefs": [
                    {
                        "sourceType": source_type_by_axis[axis_id],
                        "sourceSpan": source_span_by_axis[axis_id],
                        "excerpt": f"{axis_id.value} 的证据片段。",
                        "observationType": "narrative_observation",
                        "evidenceNote": "模型直接返回了字符串 sourceSpan。",
                        "confidence": 0.82,
                    }
                ],
                "confidence": 0.84,
                "riskTags": ["staleFormula", "unknownRisk"],
                "blockingSignals": [" 节奏仍需补强 ", "", 3],
                "affectedSkeletonDimensions": [alias_by_axis[axis_id], "ignored_alias"],
                "degradedByInput": False,
            }
            for axis_id in AxisId
        ],
        "axisSummaries": [
            {
                "axisId": axis_id.value,
                "summary": f"{axis_id.value} 总结",
                "strengths": [f"{axis_id.value} 优势"],
                "weaknesses": [f"{axis_id.value} 弱点"],
            }
            for axis_id in AxisId
        ],
        "missingRequiredAxes": ["unknownAxis"],
        "riskTags": ["staleFormula", "ignoredRisk"],
        "overallConfidence": 0.81,
    }
    provider = RecordingProviderAdapter(payloads={StageName.RUBRIC_EVALUATION: raw_payload})

    result = execute_rubric(provider_adapter=provider, context=build_rubric_context())

    assert result.taskId == "task_pipeline_001"
    assert result.schemaVersion == "schema-test-v1"
    assert result.promptVersion == "prompt-test-v1"
    assert result.rubricVersion == "rubric-test-v1"
    assert result.providerId == "provider-test"
    assert result.modelId == "model-test"
    assert result.missingRequiredAxes == []
    assert result.riskTags == [FatalRisk.STALE_FORMULA]

    hook_item = next(item for item in result.items if item.axisId is AxisId.HOOK_RETENTION)
    narrative_item = next(item for item in result.items if item.axisId is AxisId.NARRATIVE_CONTROL)
    setting_item = next(item for item in result.items if item.axisId is AxisId.SETTING_DIFFERENTIATION)

    assert hook_item.evidenceRefs[0].sourceSpan == {"chapterRef": "第一章"}
    assert narrative_item.evidenceRefs[0].sourceSpan == {"outlineRef": "全段"}
    assert setting_item.evidenceRefs[0].sourceSpan == {"crossInputRef": "chapters: 第一章; outline: 全段"}
    assert hook_item.affectedSkeletonDimensions == [SkeletonDimensionId.MARKET_ATTRACTION]
    assert narrative_item.affectedSkeletonDimensions == [SkeletonDimensionId.NARRATIVE_EXECUTION]
    assert setting_item.affectedSkeletonDimensions == [SkeletonDimensionId.NOVELTY_UTILITY]
    assert hook_item.blockingSignals == ["节奏仍需补强"]
    assert hook_item.riskTags == [FatalRisk.STALE_FORMULA]
    assert result.axisSummaries[AxisId.HOOK_RETENTION].startswith("hookRetention 总结")
    assert set(result.axisSummaries) == set(AxisId)


def test_execute_rubric_normalizes_degraded_real_deepseek_schema_drift() -> None:
    screening = build_screening_result(
        input_composition=InputComposition.CHAPTERS_OUTLINE,
        evaluation_mode=EvaluationMode.DEGRADED,
        chapters_sufficiency=Sufficiency.INSUFFICIENT,
        outline_sufficiency=Sufficiency.INSUFFICIENT,
    )
    raw_payload = {
        "taskId": "task-from-model",
        "stage": "rubric_evaluation",
        "schemaVersion": "1.0",
        "promptVersion": "1.0",
        "rubricVersion": "1.0",
        "providerId": "default",
        "modelId": "default",
        "inputComposition": "chapters_outline",
        "evaluationMode": "degraded",
        "items": [
            {
                "evaluationId": f"model-{axis_id.value}",
                "axisId": axis_id.value,
                "scoreBand": "medium" if axis_id is AxisId.PLATFORM_FIT else "low",
                "reason": f"{axis_id.value} 在当前梗概材料下只能做保守判断。",
                "evidenceRefs": [
                    {
                        "sourceType": "chapters" if axis_id in {AxisId.HOOK_RETENTION, AxisId.CHARACTER_DRIVE} else "outline",
                        "reference": f"{axis_id.value} 的摘要式证据。",
                        "sourceSpan": "第一章" if axis_id is AxisId.HOOK_RETENTION else "全段",
                    }
                ],
                "confidence": 0.42,
                "riskTags": ["insufficientMaterial"],
                "blockingSignals": [],
                "affectedSkeletonDimensions": ["conflict"],
                "degradedByInput": True,
            }
            for axis_id in AxisId
        ],
        "axisSummaries": [{ "axisId": axis_id.value, "summary": f"{axis_id.value} 总结" } for axis_id in AxisId],
        "missingRequiredAxes": ["platformFit"],
        "riskTags": ["insufficientMaterial"],
        "overallConfidence": 0.41,
    }
    provider = RecordingProviderAdapter(payloads={StageName.RUBRIC_EVALUATION: raw_payload})

    result = execute_rubric(
        provider_adapter=provider,
        context=build_rubric_context(screening=screening),
    )

    hook_item = next(item for item in result.items if item.axisId is AxisId.HOOK_RETENTION)
    platform_item = next(item for item in result.items if item.axisId is AxisId.PLATFORM_FIT)

    assert hook_item.scoreBand is ScoreBand.ONE
    assert platform_item.scoreBand is ScoreBand.TWO
    assert hook_item.evidenceRefs[0].excerpt == "hookRetention 的摘要式证据。"
    assert hook_item.evidenceRefs[0].observationType == "narrative_observation"
    assert hook_item.evidenceRefs[0].evidenceNote.startswith("由真实 provider")
    assert hook_item.evidenceRefs[0].confidence == pytest.approx(0.42)
    assert result.missingRequiredAxes == [AxisId.PLATFORM_FIT]
    assert result.riskTags == [FatalRisk.INSUFFICIENT_MATERIAL]


def test_execute_aggregation_normalizes_degraded_real_deepseek_schema_drift() -> None:
    screening = build_screening_result(
        input_composition=InputComposition.CHAPTERS_OUTLINE,
        evaluation_mode=EvaluationMode.DEGRADED,
        chapters_sufficiency=Sufficiency.INSUFFICIENT,
        outline_sufficiency=Sufficiency.SUFFICIENT,
    )
    rubric = build_rubric_set(
        input_composition=InputComposition.CHAPTERS_OUTLINE,
        evaluation_mode=EvaluationMode.DEGRADED,
    )
    raw_payload = {
        "taskId": "task-from-model",
        "stage": "aggregation",
        "schemaVersion": "1.0",
        "promptVersion": "1.0",
        "rubricVersion": "1.0",
        "providerId": "default",
        "modelId": "default",
        "axisScores": {axis_id.value: 60 + index for index, axis_id in enumerate(AxisId)},
        "skeletonScores": {dimension_id.value: 70 + index for index, dimension_id in enumerate(SkeletonDimensionId)},
        "topLevelScoresDraft": {
            "retentionScore": 61,
            "serialScore": 62,
            "characterScore": 63,
            "narrativeScore": 64,
            "settingScore": 65,
            "platformScore": 66,
            "commercialScore": 67,
        },
        "strengthCandidates": ["大纲主线稳定"],
        "weaknessCandidates": ["正文证据仍偏少"],
        "platformCandidates": ["女频平台 A"],
        "marketFitDraft": "当前材料更适合走保守市场判断。",
        "editorVerdictDraft": "建议补全正文后再复核。",
        "detailedAnalysisDraft": "聚合基于 degraded 模式，只能形成保守摘要。",
        "supportingAxisMap": {axis_id.value: [f"{axis_id.value}_1"] for axis_id in AxisId},
        "supportingSkeletonMap": {
            SkeletonDimensionId.MARKET_ATTRACTION.value: ["hookRetention_1", "serialMomentum_1"],
            SkeletonDimensionId.NARRATIVE_EXECUTION.value: ["narrativeControl_1", "pacingPayoff_1"],
            SkeletonDimensionId.CHARACTER_MOMENTUM.value: ["characterDrive_1"],
            SkeletonDimensionId.NOVELTY_UTILITY.value: ["settingDifferentiation_1"],
        },
        "riskTags": ["insufficientMaterial"],
        "overallConfidence": 0.44,
    }
    provider = RecordingProviderAdapter(payloads={StageName.AGGREGATION: raw_payload})

    result = execute_aggregation(
        provider_adapter=provider,
        context=build_aggregation_context(screening=screening, rubric=rubric),
    )

    assert result.taskId == "task_pipeline_001"
    assert result.schemaVersion == "schema-test-v1"
    assert result.promptVersion == "prompt-test-v1"
    assert result.rubricVersion == "rubric-test-v1"
    assert result.providerId == "provider-test"
    assert result.modelId == "model-test"
    assert result.topLevelScoresDraft[TopLevelScoreField.SIGNING_PROBABILITY] == 66
    assert result.topLevelScoresDraft[TopLevelScoreField.COMMERCIAL_VALUE] == 64
    assert result.detailedAnalysisDraft.plot == "聚合基于 degraded 模式，只能形成保守摘要。"
    assert result.supportingAxisMap[TopLevelScoreField.SIGNING_PROBABILITY] == [
        AxisId.PLATFORM_FIT,
        AxisId.COMMERCIAL_POTENTIAL,
    ]
    assert result.supportingSkeletonMap[TopLevelScoreField.WRITING_QUALITY] == [
        SkeletonDimensionId.NARRATIVE_EXECUTION,
    ]
    assert result.riskTags == [FatalRisk.INSUFFICIENT_MATERIAL]


def test_run_consistency_check_blocks_on_cross_input_mismatch() -> None:
    context = build_rubric_context(
        submission=build_submission(
            chapter_text="都市职场开篇出现豪门冲突与总裁对决。",
            outline_text="星际机甲战争主线已经展开并升级。",
        )
    )
    rubric = build_rubric_set()

    result = run_consistency_check(context=context, rubric=rubric)

    assert result.passed is False
    assert result.continueAllowed is False
    assert result.crossInputMismatchDetected is True
    assert result.confidence == 0.36
    assert any(conflict.conflictType is ConflictType.CROSS_INPUT_MISMATCH for conflict in result.conflicts)


def test_run_consistency_check_emits_missing_required_axis_conflict_and_blocks() -> None:
    screening = build_screening_result(
        input_composition=InputComposition.OUTLINE_ONLY,
        evaluation_mode=EvaluationMode.DEGRADED,
        has_chapters=False,
        has_outline=True,
    )
    context = build_rubric_context(
        submission=build_submission(with_chapters=False, with_outline=True),
        screening=screening,
    )
    rubric = build_rubric_set(
        input_composition=InputComposition.OUTLINE_ONLY,
        evaluation_mode=EvaluationMode.DEGRADED,
        missing_required_axes=[AxisId.PLATFORM_FIT],
    )

    result = run_consistency_check(context=context, rubric=rubric)

    assert result.passed is False
    assert result.continueAllowed is False
    assert result.missingRequiredAxes == [AxisId.PLATFORM_FIT]
    assert any(conflict.conflictType is ConflictType.MISSING_REQUIRED_AXIS for conflict in result.conflicts)


def test_run_consistency_check_blocks_on_unsupported_claims() -> None:
    unsupported_item = build_rubric_item(
        AxisId.PLATFORM_FIT,
        reason="平台适配已经形成稳定优势，结论非常明确。",
        confidence=0.8,
        evidence_confidence=0.42,
        source_type=EvidenceSourceType.CROSS_INPUT,
        excerpt="样本为空，使用 deterministic fallback。",
    )
    rubric = build_rubric_set(item_overrides={AxisId.PLATFORM_FIT: unsupported_item})

    result = run_consistency_check(context=build_rubric_context(), rubric=rubric)

    assert result.unsupportedClaimsDetected is True
    assert result.passed is False
    assert result.continueAllowed is False
    assert any(conflict.conflictType is ConflictType.UNSUPPORTED_CLAIM for conflict in result.conflicts)


def test_run_consistency_check_does_not_block_on_non_assertive_language() -> None:
    cautious_item = build_rubric_item(
        AxisId.PLATFORM_FIT,
        reason="兑现节奏仍可补强，人物动机较清晰，但平台结论仍待观察。",
        confidence=0.8,
        evidence_confidence=0.42,
        source_type=EvidenceSourceType.CROSS_INPUT,
        excerpt="样本为空，使用 deterministic fallback。",
    )
    rubric = build_rubric_set(item_overrides={AxisId.PLATFORM_FIT: cautious_item})

    result = run_consistency_check(context=build_rubric_context(), rubric=rubric)

    assert result.unsupportedClaimsDetected is False
    assert result.passed is True
    assert result.continueAllowed is True
    assert all(conflict.conflictType is not ConflictType.UNSUPPORTED_CLAIM for conflict in result.conflicts)


def test_run_consistency_check_requires_all_evidence_to_be_weak_for_unsupported_claims() -> None:
    mixed_evidence_item = build_rubric_item(
        AxisId.PLATFORM_FIT,
        reason="平台适配已经形成稳定优势，结论非常明确。",
        confidence=0.8,
        evidence_refs=[
            build_evidence(confidence=0.91, excerpt="正文中已出现稳定平台读者画像与付费意愿信号。"),
            build_evidence(
                source_type=EvidenceSourceType.CROSS_INPUT,
                confidence=0.42,
                excerpt="样本为空，使用 deterministic fallback。",
            ),
        ],
    )
    rubric = build_rubric_set(item_overrides={AxisId.PLATFORM_FIT: mixed_evidence_item})

    result = run_consistency_check(context=build_rubric_context(), rubric=rubric)

    assert result.unsupportedClaimsDetected is False
    assert result.passed is True
    assert result.continueAllowed is True
    assert all(conflict.conflictType is not ConflictType.UNSUPPORTED_CLAIM for conflict in result.conflicts)


def test_run_consistency_check_marks_duplicated_penalties_without_blocking() -> None:
    stale_formula_item = build_rubric_item(
        AxisId.HOOK_RETENTION,
        risk_tags=[FatalRisk.STALE_FORMULA],
        blocking_signals=["套路重复处罚"],
    )
    duplicate_item = build_rubric_item(
        AxisId.SERIAL_MOMENTUM,
        risk_tags=[FatalRisk.STALE_FORMULA],
        blocking_signals=["套路重复处罚"],
    )
    rubric = build_rubric_set(
        item_overrides={
            AxisId.HOOK_RETENTION: stale_formula_item,
            AxisId.SERIAL_MOMENTUM: duplicate_item,
        }
    )

    result = run_consistency_check(context=build_rubric_context(), rubric=rubric)

    assert result.duplicatedPenaltiesDetected is True
    assert result.passed is True
    assert result.continueAllowed is True
    assert any(conflict.conflictType is ConflictType.DUPLICATED_PENALTY for conflict in result.conflicts)


def test_build_final_projection_uses_primary_platform_candidate() -> None:
    aggregation = build_aggregation_result(platform_candidates=["女频平台 A", "女频平台 B"], commercial_value=81)

    projection = build_final_projection(aggregation=aggregation)

    assert [platform.name for platform in projection.platforms] == ["女频平台 A"]
    assert [platform.percentage for platform in projection.platforms] == [81]
    assert [platform.reason for platform in projection.platforms] == [aggregation.marketFitDraft]
    assert projection.detailedAnalysis == aggregation.detailedAnalysisDraft


def test_build_final_projection_does_not_fallback_platforms() -> None:
    aggregation = build_aggregation_result(platform_candidates=[])

    projection = build_final_projection(aggregation=aggregation)

    assert projection.platforms == []


def test_scoring_pipeline_blocks_with_precise_message_for_missing_required_axes() -> None:
    screening = build_screening_result(
        input_composition=InputComposition.OUTLINE_ONLY,
        evaluation_mode=EvaluationMode.DEGRADED,
        has_chapters=False,
        has_outline=True,
    )
    rubric = build_rubric_set(
        input_composition=InputComposition.OUTLINE_ONLY,
        evaluation_mode=EvaluationMode.DEGRADED,
        missing_required_axes=[AxisId.PLATFORM_FIT],
    )
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: screening.model_dump(mode="json"),
            StageName.RUBRIC_EVALUATION: rubric.model_dump(mode="json"),
            StageName.AGGREGATION: build_aggregation_result().model_dump(mode="json"),
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineBlockedError) as exc_info:
        pipeline.run(
            task=build_task(
                evaluation_mode=EvaluationMode.DEGRADED,
                input_composition=InputComposition.OUTLINE_ONLY,
            ),
            submission=build_submission(with_chapters=False, with_outline=True),
        )

    assert exc_info.value.error_code is ErrorCode.RESULT_BLOCKED
    assert "缺少必需评价轴" in exc_info.value.message
    assert "platformFit" in exc_info.value.message


def test_scoring_pipeline_uses_joint_input_mismatch_error_for_cross_input_conflict() -> None:
    screening = build_screening_result()
    rubric = build_rubric_set()
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: screening.model_dump(mode="json"),
            StageName.RUBRIC_EVALUATION: rubric.model_dump(mode="json"),
            StageName.AGGREGATION: build_aggregation_result().model_dump(mode="json"),
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineBlockedError) as exc_info:
        pipeline.run(
            task=build_task(),
            submission=build_submission(
                chapter_text="都市豪门冲突已经爆发并持续升级。",
                outline_text="星际机甲远征主线进入宇宙战争。",
            ),
        )

    assert exc_info.value.error_code is ErrorCode.JOINT_INPUT_MISMATCH
    assert "正文与大纲之间存在高严重度冲突" in exc_info.value.message


def test_scoring_pipeline_raises_stage_schema_invalid_when_aggregation_payload_invalid() -> None:
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: build_screening_result().model_dump(mode="json"),
            StageName.RUBRIC_EVALUATION: build_rubric_set().model_dump(mode="json"),
            StageName.AGGREGATION: {"taskId": "task_pipeline_001", "stage": "aggregation"},
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.STAGE_SCHEMA_INVALID
    assert "aggregation 阶段输出不满足正式 schema" in exc_info.value.message


def test_scoring_pipeline_happy_path_resolves_runtime_by_screening_output() -> None:
    screening = build_screening_result()
    rubric = build_rubric_set()
    aggregation = build_aggregation_result()
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: screening.model_dump(mode="json"),
            StageName.RUBRIC_EVALUATION: rubric.model_dump(mode="json"),
            StageName.AGGREGATION: aggregation.model_dump(mode="json"),
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    result = pipeline.run(task=build_task(), submission=build_submission())

    assert result.projection.platforms[0].name == "女频平台 A"
    assert prompt_runtime.calls == [
        {
            "stage": "input_screening",
            "input_composition": "chapters_outline",
            "evaluation_mode": "full",
            "provider_id": "provider-test",
            "model_id": "model-test",
        },
        {
            "stage": "rubric_evaluation",
            "input_composition": "chapters_outline",
            "evaluation_mode": "full",
            "provider_id": "provider-test",
            "model_id": "model-test",
        },
        {
            "stage": "aggregation",
            "input_composition": "chapters_outline",
            "evaluation_mode": "full",
            "provider_id": "provider-test",
            "model_id": "model-test",
        },
    ]
    assert [
        {
            "stage": request.stage.value,
            "timeoutMs": request.timeoutMs,
            "maxTokens": request.maxTokens,
            "responseFormat": request.responseFormat,
        }
        for request in provider.requests
    ] == [
        {
            "stage": "input_screening",
            "timeoutMs": 90_000,
            "maxTokens": 1_500,
            "responseFormat": {"type": "json_object"},
        },
        {
            "stage": "rubric_evaluation",
            "timeoutMs": 90_000,
            "maxTokens": 6_000,
            "responseFormat": {"type": "json_object"},
        },
        {
            "stage": "aggregation",
            "timeoutMs": 90_000,
            "maxTokens": 4_000,
            "responseFormat": {"type": "json_object"},
        },
    ]
