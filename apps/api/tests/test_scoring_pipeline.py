from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
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
from packages.application.scoring_pipeline.rubric_executor import execute_rubric, execute_rubric_slice
from packages.application.scoring_pipeline.screening_executor import execute_screening
from packages.schemas.common.enums import (
    AxisId,
    EvaluationMode,
    EvidenceSourceType,
    FatalRisk,
    InputComposition,
    NovelType,
    ResultStatus,
    ScoreBand,
    SkeletonDimensionId,
    StageName,
    StageStatus,
    Sufficiency,
    TaskStatus,
)
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline
from packages.schemas.input.screening import InputScreeningResult
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.task import EvaluationTask
from packages.schemas.stages.aggregation import AggregatedRubricResult, PlatformCandidate
from packages.schemas.stages.consistency import ConflictType
from packages.schemas.stages.rubric import RubricEvaluationEvidenceRef, RubricEvaluationItem, RubricEvaluationSet
from packages.schemas.stages.type_classification import TypeClassificationCandidate, TypeClassificationResult
from packages.schemas.stages.type_lens import TypeLensEvaluationResult, TypeLensItem


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


@dataclass(frozen=True, slots=True)
class StubProviderFailure:
    failureType: str
    message: str
    rawJson: Any = None


@dataclass(frozen=True, slots=True)
class StubProviderSuccessWithoutRawJson:
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

    def execute(self, request: Any) -> StubProviderSuccess | StubProviderFailure:
        self.requests.append(request)
        payload = self.payloads[request.stage]
        if callable(payload):
            payload = payload(request)
        if isinstance(payload, StubProviderFailure):
            return payload
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


def build_platform_candidate(name: str, weight: int, pitch_quote: str) -> PlatformCandidate:
    return PlatformCandidate(name=name, weight=weight, pitchQuote=pitch_quote)


def build_aggregation_result(
    *,
    platform_candidates: list[PlatformCandidate] | None = None,
    market_fit: str = "当前题材更贴合女频平台 A 的用户预期。",
    overall_summary: str = "章节主线与市场抓手已形成初步可读的总体判断。",
    overall_verdict: str = "建议继续观察并进入样章复核。",
    overall_confidence: float = 0.82,
) -> AggregatedRubricResult:
    default_candidates = [
        build_platform_candidate("女频平台 A", 70, "情感流向与平台核心读者群体高度匹配。"),
        build_platform_candidate("女频平台 B", 30, "题材定位次级适配，可作为备选投放渠道。"),
    ]
    return AggregatedRubricResult(
        taskId="task_pipeline_001",
        stage=StageName.AGGREGATION,
        schemaVersion="schema-test-v1",
        promptVersion="prompt-test-v1",
        rubricVersion="rubric-test-v1",
        providerId="provider-test",
        modelId="model-test",
        overallVerdictDraft=overall_verdict,
        overallSummaryDraft=overall_summary,
        platformCandidates=platform_candidates if platform_candidates is not None else default_candidates,
        marketFitDraft=market_fit,
        riskTags=[],
        overallConfidence=overall_confidence,
    )


def build_type_classification_result(
    *,
    novel_type: NovelType = NovelType.URBAN_REALITY,
    classification_confidence: float = 0.78,
    fallback_used: bool = False,
    input_composition: InputComposition = InputComposition.CHAPTERS_OUTLINE,
    evaluation_mode: EvaluationMode = EvaluationMode.FULL,
) -> TypeClassificationResult:
    secondary_novel_type = (
        NovelType.URBAN_REALITY
        if novel_type in {NovelType.FANTASY_UPGRADE, NovelType.GENERAL_FALLBACK}
        else NovelType.FANTASY_UPGRADE
    )
    tertiary_novel_type = (
        NovelType.GAME_DERIVATIVE
        if novel_type is not NovelType.GAME_DERIVATIVE and secondary_novel_type is not NovelType.GAME_DERIVATIVE
        else NovelType.HISTORY_MILITARY
    )
    candidates = [
        TypeClassificationCandidate(
            novelType=novel_type,
            confidence=classification_confidence,
            reason="当前题材信号最稳定。",
        ),
        TypeClassificationCandidate(
            novelType=secondary_novel_type,
            confidence=max(0.2, round(classification_confidence - 0.18, 2)),
            reason="存在次级题材信号。",
        ),
        TypeClassificationCandidate(
            novelType=tertiary_novel_type,
            confidence=max(0.15, round(classification_confidence - 0.29, 2)),
            reason="保守兜底候选。",
        ),
    ]
    return TypeClassificationResult(
        taskId="task_pipeline_001",
        schemaVersion="schema-test-v1",
        promptVersion="prompt-test-v1",
        rubricVersion="rubric-test-v1",
        providerId="provider-test",
        modelId="model-test",
        inputComposition=input_composition,
        evaluationMode=evaluation_mode,
        candidates=candidates,
        novelType=NovelType.GENERAL_FALLBACK if fallback_used else novel_type,
        classificationConfidence=classification_confidence,
        fallbackUsed=fallback_used,
        summary="类型信号已形成稳定候选集。",
    )


def build_type_lens_result(
    *,
    novel_type: NovelType = NovelType.URBAN_REALITY,
    input_composition: InputComposition = InputComposition.CHAPTERS_OUTLINE,
    evaluation_mode: EvaluationMode = EvaluationMode.FULL,
    score_band: ScoreBand = ScoreBand.THREE,
) -> TypeLensEvaluationResult:
    lens_map = {
        NovelType.FEMALE_GENERAL: [
            ("emotionImmersion", "情绪钩子与代入"),
            ("relationshipAppeal", "关系张力与人物吸引"),
            ("emotionPayoff", "情绪递进与兑现"),
            ("companionshipValue", "圈层承诺与陪伴价值"),
        ],
        NovelType.FANTASY_UPGRADE: [
            ("upgradeLoop", "升级回路清晰度"),
            ("powerSystem", "力量体系可读性"),
            ("rewardDensity", "奖励密度"),
            ("spectaclePayoff", "奇观/爽点兑现"),
        ],
        NovelType.URBAN_REALITY: [
            ("realityHook", "现实抓手"),
            ("mobilityTension", "地位跃迁/经营张力"),
            ("industryCredibility", "行业/现实可信度"),
            ("conversionHook", "连载转化抓手"),
        ],
        NovelType.HISTORY_MILITARY: [
            ("powerMap", "权力/战争格局清晰度"),
            ("historicalTexture", "历史质感与可信度"),
            ("strategyPayoff", "谋略兑现"),
            ("campaignMomentum", "长线争霸推进"),
        ],
        NovelType.SCI_FI_APOCALYPSE: [
            ("conceptUtility", "概念可利用度"),
            ("ruleClosure", "规则闭环"),
            ("pressureSystem", "生存/技术压力系统"),
            ("worldExpansion", "世界扩展潜力"),
        ],
        NovelType.SUSPENSE_HORROR: [
            ("mysteryHook", "谜面钩子"),
            ("clueFairness", "线索公平性"),
            ("tensionSustain", "紧张维持"),
            ("revealPayoff", "揭示兑现"),
        ],
        NovelType.GAME_DERIVATIVE: [
            ("loopClarity", "副本/循环清晰度"),
            ("ruleFeedback", "规则反馈明确性"),
            ("buildVariation", "build/玩法变化"),
            ("longRunEscalation", "长线 escalations"),
        ],
        NovelType.GENERAL_FALLBACK: [
            ("premiseHook", "premise 与钩子"),
            ("coreConflict", "核心冲突与目标"),
            ("executionReadability", "执行与可读性"),
            ("serialPotential", "连载潜力"),
        ],
    }
    items = [
        TypeLensItem(
            lensId=lens_id,
            label=label,
            scoreBand=score_band,
            reason=f"{label} 证据完整。",
            evidenceRefs=[build_evidence()],
            confidence=0.8 if evaluation_mode is EvaluationMode.FULL else 0.58,
            riskTags=[FatalRisk.INSUFFICIENT_MATERIAL] if evaluation_mode is EvaluationMode.DEGRADED else [],
            degradedByInput=evaluation_mode is EvaluationMode.DEGRADED,
        )
        for lens_id, label in lens_map[novel_type]
    ]
    return TypeLensEvaluationResult(
        taskId="task_pipeline_001",
        schemaVersion="schema-test-v1",
        promptVersion="prompt-test-v1",
        rubricVersion="rubric-test-v1",
        providerId="provider-test",
        modelId="model-test",
        inputComposition=input_composition,
        evaluationMode=evaluation_mode,
        novelType=novel_type,
        summary="类型 lens 结果稳定。",
        items=items,
        overallConfidence=min(item.confidence for item in items),
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


def build_rubric_slice_payload(*, requested_axes: list[AxisId]) -> dict[str, Any]:
    return {
        "requestedAxes": [axis_id.value for axis_id in requested_axes],
        "items": [
            {
                "evaluationId": f"eval-{axis_id.value}",
                "axisId": axis_id.value,
                "scoreBand": ScoreBand.THREE.value,
                "reason": f"{axis_id.value} 的判断依据完整。",
                "evidenceRefs": [
                    {
                        "sourceType": EvidenceSourceType.CHAPTERS.value,
                        "sourceSpan": {"chapterIndex": 0},
                        "excerpt": f"{axis_id.value} 的证据片段。",
                        "observationType": "narrative_observation",
                        "evidenceNote": "用于说明判断依据",
                        "confidence": 0.82,
                    }
                ],
                "confidence": 0.84,
                "riskTags": [],
                "blockingSignals": [],
                "affectedSkeletonDimensions": [SkeletonDimensionId.MARKET_ATTRACTION.value],
                "degradedByInput": False,
            }
            for axis_id in requested_axes
        ],
        "axisSummaries": [
            {"axisId": axis_id.value, "summary": f"{axis_id.value} 总结"}
            for axis_id in requested_axes
        ],
        "missingRequiredAxes": [],
        "riskTags": [],
        "overallConfidence": 0.81,
    }


def build_aggregation_context(
    *,
    submission: JointSubmissionRequest | None = None,
    screening: InputScreeningResult | None = None,
    rubric: RubricEvaluationSet | None = None,
    type_classification: TypeClassificationResult | None = None,
    type_lens: TypeLensEvaluationResult | None = None,
) -> AggregationExecutionContext:
    resolved_submission = submission or build_submission()
    resolved_screening = screening or build_screening_result()
    resolved_rubric = rubric or build_rubric_set(
        input_composition=resolved_screening.inputComposition,
        evaluation_mode=resolved_screening.evaluationMode,
    )
    resolved_type_classification = type_classification or build_type_classification_result()
    resolved_type_lens = type_lens or build_type_lens_result(
        novel_type=resolved_type_classification.novelType,
        evaluation_mode=resolved_screening.evaluationMode,
    )
    rubric_context = build_rubric_context(submission=resolved_submission, screening=resolved_screening)
    consistency = run_consistency_check(context=rubric_context, rubric=resolved_rubric)
    return AggregationExecutionContext(
        task_id="task_pipeline_001",
        submission=resolved_submission,
        screening=resolved_screening,
        type_classification=resolved_type_classification,
        rubric=resolved_rubric,
        type_lens=resolved_type_lens,
        consistency=consistency,
        binding=build_stage_binding(stage=StageName.AGGREGATION),
    )


def build_pipeline_provider_payloads(
    *,
    screening: InputScreeningResult | None = None,
    type_classification: TypeClassificationResult | None = None,
    type_lens: TypeLensEvaluationResult | None = None,
    rubric_payload: Any = None,
    aggregation_payload: Any = None,
) -> dict[StageName, Any]:
    resolved_screening = screening or build_screening_result()
    resolved_type_classification = type_classification or build_type_classification_result(
        input_composition=resolved_screening.inputComposition,
        evaluation_mode=resolved_screening.evaluationMode,
    )
    resolved_type_lens = type_lens or build_type_lens_result(
        novel_type=resolved_type_classification.novelType,
        input_composition=resolved_screening.inputComposition,
        evaluation_mode=resolved_screening.evaluationMode,
    )
    return {
        StageName.INPUT_SCREENING: resolved_screening.model_dump(mode="json"),
        StageName.TYPE_CLASSIFICATION: resolved_type_classification.model_dump(mode="json"),
        StageName.RUBRIC_EVALUATION: rubric_payload,
        StageName.TYPE_LENS_EVALUATION: resolved_type_lens.model_dump(mode="json"),
        StageName.AGGREGATION: aggregation_payload if aggregation_payload is not None else build_aggregation_result().model_dump(mode="json"),
    }


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
    raw_payloads = [
        {
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
                for axis_id in requested_axes
            ],
            "axisSummaries": [
                {
                    "axisId": axis_id.value,
                    "summary": f"{axis_id.value} 总结",
                    "strengths": [f"{axis_id.value} 优势"],
                    "weaknesses": [f"{axis_id.value} 弱点"],
                }
                for axis_id in requested_axes
            ],
            "missingRequiredAxes": ["unknownAxis"],
            "riskTags": ["staleFormula", "ignoredRisk"],
            "overallConfidence": 0.81,
        }
        for requested_axes in [
            [AxisId.HOOK_RETENTION, AxisId.SERIAL_MOMENTUM, AxisId.CHARACTER_DRIVE],
            [AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF, AxisId.SETTING_DIFFERENTIATION],
            [AxisId.PLATFORM_FIT, AxisId.COMMERCIAL_POTENTIAL],
        ]
    ]
    rubric_call_index = {"value": 0}

    def provide_rubric_payload(request: Any) -> dict[str, Any]:
        payload = raw_payloads[rubric_call_index["value"]]
        rubric_call_index["value"] += 1
        return payload

    provider = RecordingProviderAdapter(payloads={StageName.RUBRIC_EVALUATION: provide_rubric_payload})

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
    raw_payloads = [
        {
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
                for axis_id in requested_axes
            ],
            "axisSummaries": [{ "axisId": axis_id.value, "summary": f"{axis_id.value} 总结" } for axis_id in requested_axes],
            "missingRequiredAxes": ["platformFit"] if AxisId.PLATFORM_FIT in requested_axes else [],
            "riskTags": ["insufficientMaterial"],
            "overallConfidence": 0.41,
        }
        for requested_axes in [
            [AxisId.HOOK_RETENTION, AxisId.SERIAL_MOMENTUM, AxisId.CHARACTER_DRIVE],
            [AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF, AxisId.SETTING_DIFFERENTIATION],
            [AxisId.PLATFORM_FIT, AxisId.COMMERCIAL_POTENTIAL],
        ]
    ]
    rubric_call_index = {"value": 0}

    def provide_rubric_payload(request: Any) -> dict[str, Any]:
        payload = raw_payloads[rubric_call_index["value"]]
        rubric_call_index["value"] += 1
        return payload

    provider = RecordingProviderAdapter(payloads={StageName.RUBRIC_EVALUATION: provide_rubric_payload})

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
    assert result.missingRequiredAxes == []
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
        "platformCandidates": [
            {"name": "女频平台 A", "weight": 100, "pitchQuote": "降级模式下保守推荐，题材基本适配。"},
        ],
        "marketFitDraft": "当前材料更适合走保守市场判断。",
        "editorVerdictDraft": "建议补全正文后再复核。",
        "verdictSubQuote": "降级评估结论保守，材料补全后可重新判断市场承接能力。",
        "detailedAnalysisDraft": "聚合基于 degraded 模式，只能形成保守摘要。",
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
    assert result.overallVerdictDraft == "建议补全正文后再复核。"
    assert result.verdictSubQuote == "降级评估结论保守，材料补全后可重新判断市场承接能力。"
    assert result.overallSummaryDraft == "聚合基于 degraded 模式，只能形成保守摘要。"
    assert len(result.platformCandidates) == 1
    assert result.platformCandidates[0].name == "女频平台 A"
    assert result.platformCandidates[0].weight == 100
    assert result.marketFitDraft == "当前材料更适合走保守市场判断。"
    assert result.riskTags == [FatalRisk.INSUFFICIENT_MATERIAL]
    assert result.overallConfidence == pytest.approx(0.44)


def test_execute_rubric_retries_once_after_schema_invalid_payload() -> None:
    requested_axes = [AxisId.HOOK_RETENTION, AxisId.SERIAL_MOMENTUM, AxisId.CHARACTER_DRIVE]
    invalid_payload = build_rubric_slice_payload(requested_axes=requested_axes)
    invalid_payload["items"] = invalid_payload["items"][:2]
    invalid_payload["axisSummaries"] = invalid_payload["axisSummaries"][:2]
    payloads = [invalid_payload, build_rubric_slice_payload(requested_axes=requested_axes)]
    call_index = {"value": 0}

    def provide_payload(request: Any) -> dict[str, Any]:
        payload = payloads[call_index["value"]]
        call_index["value"] += 1
        return payload

    provider = RecordingProviderAdapter(payloads={StageName.RUBRIC_EVALUATION: provide_payload})

    result = execute_rubric_slice(
        provider_adapter=provider,
        context=RubricExecutionContext(
            task_id="task_pipeline_001",
            submission=build_submission(),
            screening=build_screening_result(),
            binding=build_stage_binding(stage=StageName.RUBRIC_EVALUATION),
            requested_axes=tuple(requested_axes),
        ),
    )

    assert [item.axisId for item in result.items] == requested_axes
    assert len([request for request in provider.requests if request.stage is StageName.RUBRIC_EVALUATION]) == 2


def test_execute_aggregation_retries_once_after_schema_invalid_payload() -> None:
    payloads: list[Any] = [["invalid-payload"], build_aggregation_result().model_dump(mode="json")]
    call_index = {"value": 0}

    def provide_payload(request: Any) -> Any:
        payload = payloads[call_index["value"]]
        call_index["value"] += 1
        return payload

    provider = RecordingProviderAdapter(payloads={StageName.AGGREGATION: provide_payload})

    result = execute_aggregation(provider_adapter=provider, context=build_aggregation_context())

    assert result.overallVerdictDraft == "建议继续观察并进入样章复核。"
    assert len([request for request in provider.requests if request.stage is StageName.AGGREGATION]) == 2



def test_execute_aggregation_fail_fast_on_empty_mapping_payload() -> None:
    provider = RecordingProviderAdapter(payloads={StageName.AGGREGATION: {}})

    with pytest.raises(PipelineFailureError) as exc_info:
        execute_aggregation(
            provider_adapter=provider,
            context=build_aggregation_context(),
        )

    assert exc_info.value.error_code is ErrorCode.STAGE_SCHEMA_INVALID
    assert "aggregation 阶段输出不满足正式 schema" in exc_info.value.message



def test_execute_aggregation_fail_fast_on_weak_mapping_payload() -> None:
    provider = RecordingProviderAdapter(
        payloads={
            StageName.AGGREGATION: {
                "overallVerdictDraft": MappingProxyType({}),
                "overallSummaryDraft": MappingProxyType({}),
                "marketFitDraft": MappingProxyType({}),
                "platformCandidates": MappingProxyType({}),
                "riskTags": MappingProxyType({}),
                "overallConfidence": MappingProxyType({}),
            }
        }
    )

    with pytest.raises(PipelineFailureError) as exc_info:
        execute_aggregation(
            provider_adapter=provider,
            context=build_aggregation_context(),
        )

    assert exc_info.value.error_code is ErrorCode.STAGE_SCHEMA_INVALID
    assert "aggregation 阶段输出不满足正式 schema" in exc_info.value.message


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


def test_run_consistency_check_marks_suspected_cross_input_divergence_without_blocking() -> None:
    context = build_rubric_context(
        submission=build_submission(
            chapter_text="都市开篇冲突已经抛出，但题材承诺仍需更多正文确认。",
            outline_text="星际主线已经启动，不过目前只给出单点设定提示。",
        )
    )
    rubric = build_rubric_set()

    result = run_consistency_check(context=context, rubric=rubric)

    assert result.passed is True
    assert result.continueAllowed is True
    assert result.crossInputMismatchDetected is False
    assert result.confidence == 0.78
    assert any("疑似题材分歧" in note for note in result.normalizationNotes)
    assert all(conflict.conflictType is not ConflictType.CROSS_INPUT_MISMATCH for conflict in result.conflicts)


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


def test_build_final_projection_uses_overall_fields() -> None:
    candidates = [
        build_platform_candidate("女频平台 A", 70, "情感流向与平台核心读者群体高度匹配。"),
        build_platform_candidate("女频平台 B", 30, "题材定位次级适配，可作为备选投放渠道。"),
    ]
    aggregation = build_aggregation_result(platform_candidates=candidates, market_fit="当前题材更贴合女频平台 A 的用户预期。")
    type_classification = build_type_classification_result()
    rubric = build_rubric_set()
    type_lens = build_type_lens_result(novel_type=type_classification.novelType)
    consistency = run_consistency_check(context=build_rubric_context(), rubric=rubric)

    projection = build_final_projection(
        aggregation=aggregation,
        type_classification=type_classification,
        rubric=rubric,
        type_lens=type_lens,
        consistency=consistency,
    )

    assert len(projection.axes) == len(AxisId)
    assert projection.overall.score == 75
    assert projection.overall.verdict == aggregation.overallVerdictDraft
    assert projection.overall.summary == aggregation.overallSummaryDraft
    assert len(projection.overall.platformCandidates) == 2
    assert projection.overall.platformCandidates[0].name == "女频平台 A"
    assert projection.overall.platformCandidates[0].weight == 70
    assert projection.overall.marketFit == aggregation.marketFitDraft
    assert projection.overall.strengths == aggregation.strengthCandidates
    assert projection.overall.weaknesses == aggregation.weaknessCandidates
    assert projection.typeAssessment is not None
    assert projection.typeAssessment.novelType is NovelType.URBAN_REALITY
    assert len(projection.typeAssessment.lenses) == 4


def test_build_final_projection_preserves_empty_platform_candidates() -> None:
    aggregation = build_aggregation_result(platform_candidates=[])
    type_classification = build_type_classification_result()
    rubric = build_rubric_set()
    type_lens = build_type_lens_result(novel_type=type_classification.novelType)
    consistency = run_consistency_check(context=build_rubric_context(), rubric=rubric)

    projection = build_final_projection(
        aggregation=aggregation,
        type_classification=type_classification,
        rubric=rubric,
        type_lens=type_lens,
        consistency=consistency,
    )

    assert projection.overall.platformCandidates == []
    assert projection.overall.verdictSubQuote is None
    assert projection.overall.strengths == []
    assert projection.overall.weaknesses == []


def test_build_final_projection_applies_type_weights_and_degraded_penalty() -> None:
    aggregation = build_aggregation_result()
    rubric = build_rubric_set(evaluation_mode=EvaluationMode.DEGRADED)
    consistency = run_consistency_check(
        context=build_rubric_context(screening=build_screening_result(evaluation_mode=EvaluationMode.DEGRADED)),
        rubric=rubric,
    )
    weighted_type_classification = build_type_classification_result(
        novel_type=NovelType.FANTASY_UPGRADE,
        input_composition=InputComposition.CHAPTERS_OUTLINE,
        evaluation_mode=EvaluationMode.DEGRADED,
    )
    weighted_type_lens = build_type_lens_result(
        novel_type=weighted_type_classification.novelType,
        input_composition=InputComposition.CHAPTERS_OUTLINE,
        evaluation_mode=EvaluationMode.DEGRADED,
        score_band=ScoreBand.FOUR,
    )
    fallback_type_classification = build_type_classification_result(
        novel_type=NovelType.FANTASY_UPGRADE,
        fallback_used=True,
        input_composition=InputComposition.CHAPTERS_OUTLINE,
        evaluation_mode=EvaluationMode.DEGRADED,
    )
    fallback_type_lens = build_type_lens_result(
        novel_type=fallback_type_classification.novelType,
        input_composition=InputComposition.CHAPTERS_OUTLINE,
        evaluation_mode=EvaluationMode.DEGRADED,
        score_band=ScoreBand.FOUR,
    )

    weighted_projection = build_final_projection(
        aggregation=aggregation,
        type_classification=weighted_type_classification,
        rubric=rubric,
        type_lens=weighted_type_lens,
        consistency=consistency,
    )
    fallback_projection = build_final_projection(
        aggregation=aggregation,
        type_classification=fallback_type_classification,
        rubric=rubric,
        type_lens=fallback_type_lens,
        consistency=consistency,
    )

    assert weighted_projection.overall.score == 71
    assert fallback_projection.overall.score == 69
    assert fallback_projection.typeAssessment is not None
    assert fallback_projection.typeAssessment.fallbackUsed is True
    assert fallback_projection.typeAssessment.novelType is NovelType.GENERAL_FALLBACK


def test_scoring_pipeline_raises_stage_schema_invalid_when_slice_omits_requested_axis() -> None:
    screening = build_screening_result(
        input_composition=InputComposition.OUTLINE_ONLY,
        evaluation_mode=EvaluationMode.DEGRADED,
        has_chapters=False,
        has_outline=True,
    )
    prompt_runtime = RecordingPromptRuntime()

    def provide_rubric_payload(request: Any) -> dict[str, Any]:
        requested_axes = [AxisId(value) for value in json.loads(request.messages[-1].content)["requestedAxes"]]
        payload = build_rubric_slice_payload(requested_axes=requested_axes)
        if AxisId.PLATFORM_FIT in requested_axes:
            payload["items"] = [item for item in payload["items"] if item["axisId"] != AxisId.PLATFORM_FIT.value]
        return payload

    provider = RecordingProviderAdapter(
        payloads=build_pipeline_provider_payloads(
            screening=screening,
            type_classification=build_type_classification_result(
                novel_type=NovelType.GENERAL_FALLBACK,
                fallback_used=True,
                input_composition=screening.inputComposition,
                evaluation_mode=screening.evaluationMode,
            ),
            type_lens=build_type_lens_result(
                novel_type=NovelType.GENERAL_FALLBACK,
                input_composition=screening.inputComposition,
                evaluation_mode=screening.evaluationMode,
            ),
            rubric_payload=provide_rubric_payload,
        )
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(
            task=build_task(
                evaluation_mode=EvaluationMode.DEGRADED,
                input_composition=InputComposition.OUTLINE_ONLY,
            ),
            submission=build_submission(with_chapters=False, with_outline=True),
        )

    assert exc_info.value.error_code is ErrorCode.STAGE_SCHEMA_INVALID
    assert "rubric_evaluation" in exc_info.value.message


def test_scoring_pipeline_uses_joint_input_mismatch_error_for_cross_input_conflict() -> None:
    screening = build_screening_result()
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads=build_pipeline_provider_payloads(
            screening=screening,
            rubric_payload=lambda request: build_rubric_slice_payload(
                requested_axes=[AxisId(value) for value in json.loads(request.messages[-1].content)["requestedAxes"]]
            ),
        )
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



def test_scoring_pipeline_allows_weak_cross_input_divergence_to_continue() -> None:
    screening = build_screening_result()
    aggregation = build_aggregation_result()
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads=build_pipeline_provider_payloads(
            screening=screening,
            rubric_payload=lambda request: build_rubric_slice_payload(
                requested_axes=[AxisId(value) for value in json.loads(request.messages[-1].content)["requestedAxes"]]
            ),
            aggregation_payload=aggregation.model_dump(mode="json"),
        )
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    result = pipeline.run(
        task=build_task(),
        submission=build_submission(
            chapter_text="都市开篇冲突已经抛出，但题材承诺仍需更多正文确认。",
            outline_text="星际主线已经启动，不过目前只给出单点设定提示。",
        ),
    )

    assert result.consistency.crossInputMismatchDetected is False
    assert result.consistency.continueAllowed is True
    assert result.consistency.confidence == 0.78
    assert any("疑似题材分歧" in note for note in result.consistency.normalizationNotes)
    assert result.projection.overall.verdict == aggregation.overallVerdictDraft


def test_scoring_pipeline_masks_screening_rejection_reason_message() -> None:
    screening = build_screening_result(
        evaluation_mode=EvaluationMode.DEGRADED,
        chapters_sufficiency=Sufficiency.INSUFFICIENT,
        outline_sufficiency=Sufficiency.SUFFICIENT,
        continue_allowed=False,
        rateable=False,
        rejection_reasons=["raw upstream provider reason sk-secret should not leak"],
    )
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: screening.model_dump(mode="json"),
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineBlockedError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.INSUFFICIENT_CHAPTERS_INPUT
    assert exc_info.value.message == "正文内容不足，当前无法进入正式评分，请补充正文后重试。"
    assert "raw upstream" not in exc_info.value.message
    assert "sk-secret" not in exc_info.value.message



def test_scoring_pipeline_masks_outline_screening_rejection_reason_message() -> None:
    screening = build_screening_result(
        input_composition=InputComposition.OUTLINE_ONLY,
        evaluation_mode=EvaluationMode.DEGRADED,
        has_chapters=False,
        has_outline=True,
        chapters_sufficiency=Sufficiency.MISSING,
        outline_sufficiency=Sufficiency.INSUFFICIENT,
        continue_allowed=False,
        rateable=False,
        rejection_reasons=["outline upstream provider reason sk-secret should not leak"],
    )
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: screening.model_dump(mode="json"),
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

    assert exc_info.value.error_code is ErrorCode.INSUFFICIENT_OUTLINE_INPUT
    assert exc_info.value.message == "大纲内容不足，当前无法进入正式评分，请补充大纲后重试。"
    assert "upstream" not in exc_info.value.message
    assert "sk-secret" not in exc_info.value.message



def test_scoring_pipeline_masks_joint_unrateable_screening_rejection_reason_message() -> None:
    screening = build_screening_result(
        evaluation_mode=EvaluationMode.DEGRADED,
        chapters_sufficiency=Sufficiency.SUFFICIENT,
        outline_sufficiency=Sufficiency.SUFFICIENT,
        continue_allowed=False,
        rateable=False,
        rejection_reasons=["joint upstream provider reason sk-secret should not leak"],
    )
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: screening.model_dump(mode="json"),
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineBlockedError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.JOINT_INPUT_UNRATEABLE
    assert exc_info.value.message == "输入材料未满足正式评分条件，当前无法进入正式评分，请补充材料后重试。"
    assert "upstream" not in exc_info.value.message
    assert "sk-secret" not in exc_info.value.message


def test_scoring_pipeline_raises_stage_schema_invalid_when_aggregation_payload_invalid() -> None:
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads=build_pipeline_provider_payloads(
            screening=build_screening_result(),
            rubric_payload=lambda request: build_rubric_slice_payload(
                requested_axes=[AxisId(value) for value in json.loads(request.messages[-1].content)["requestedAxes"]]
            ),
            aggregation_payload=["invalid-payload"],
        )
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.STAGE_SCHEMA_INVALID
    assert "aggregation 阶段输出不满足正式 schema" in exc_info.value.message



def test_scoring_pipeline_masks_provider_failure_message() -> None:
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: StubProviderFailure(
                failureType="provider_failure",
                message="upstream raw error: invalid api key sk-test-secret",
            ),
            StageName.RUBRIC_EVALUATION: lambda request: build_rubric_slice_payload(requested_axes=[AxisId(value) for value in json.loads(request.messages[-1].content)["requestedAxes"]]),
            StageName.AGGREGATION: build_aggregation_result().model_dump(mode="json"),
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.PROVIDER_FAILURE
    assert "invalid api key" not in exc_info.value.message
    assert "sk-test-secret" not in exc_info.value.message
    assert "upstream raw error" not in exc_info.value.message



def test_scoring_pipeline_maps_unknown_provider_failure_type_to_sanitized_provider_failure() -> None:
    prompt_runtime = RecordingPromptRuntime()
    provider = RecordingProviderAdapter(
        payloads={
            StageName.INPUT_SCREENING: StubProviderFailure(
                failureType="provider_new_failure",
                message="upstream raw error: req-secret-001",
            ),
            StageName.RUBRIC_EVALUATION: lambda request: build_rubric_slice_payload(requested_axes=[AxisId(value) for value in json.loads(request.messages[-1].content)["requestedAxes"]]),
            StageName.AGGREGATION: build_aggregation_result().model_dump(mode="json"),
        }
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.PROVIDER_FAILURE
    assert "req-secret-001" not in exc_info.value.message
    assert "provider_new_failure" not in exc_info.value.message



def test_scoring_pipeline_masks_provider_exception_message() -> None:
    prompt_runtime = RecordingPromptRuntime()

    class RaisingProviderAdapter:
        provider_id = "provider-test"
        model_id = "model-test"

        def execute(self, request: Any) -> StubProviderSuccess:
            raise RuntimeError("provider exploded with token sk-live-secret")

    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=RaisingProviderAdapter())

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.PROVIDER_FAILURE
    assert "sk-live-secret" not in exc_info.value.message
    assert "provider exploded" not in exc_info.value.message



def test_scoring_pipeline_maps_timeout_exception_to_timeout_error() -> None:
    prompt_runtime = RecordingPromptRuntime()

    class APITimeoutError(Exception):
        pass

    class RaisingTimeoutProviderAdapter:
        provider_id = "provider-test"
        model_id = "model-test"

        def execute(self, request: Any) -> StubProviderSuccess:
            raise APITimeoutError("provider timeout with token sk-timeout-secret")

    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=RaisingTimeoutProviderAdapter())

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.TIMEOUT
    assert "sk-timeout-secret" not in exc_info.value.message



def test_scoring_pipeline_raises_contract_invalid_when_success_payload_missing_raw_json() -> None:
    prompt_runtime = RecordingPromptRuntime()

    class MissingRawJsonProviderAdapter:
        provider_id = "provider-test"
        model_id = "model-test"

        def execute(self, request: Any) -> StubProviderSuccessWithoutRawJson:
            return StubProviderSuccessWithoutRawJson()

    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=MissingRawJsonProviderAdapter())

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.CONTRACT_INVALID
    assert "rawJson" not in exc_info.value.message


def test_scoring_pipeline_happy_path_resolves_runtime_by_screening_output() -> None:
    screening = build_screening_result()
    type_classification = build_type_classification_result(
        novel_type=NovelType.FANTASY_UPGRADE,
        input_composition=screening.inputComposition,
        evaluation_mode=screening.evaluationMode,
    )
    aggregation = build_aggregation_result()
    requested_axes_batches = [
        [AxisId.HOOK_RETENTION, AxisId.SERIAL_MOMENTUM, AxisId.CHARACTER_DRIVE],
        [AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF, AxisId.SETTING_DIFFERENTIATION],
        [AxisId.PLATFORM_FIT, AxisId.COMMERCIAL_POTENTIAL],
    ]
    rubric_payloads = [build_rubric_slice_payload(requested_axes=batch) for batch in requested_axes_batches]
    prompt_runtime = RecordingPromptRuntime()

    rubric_call_index = {"value": 0}

    def provide_rubric_payload(request: Any) -> dict[str, Any]:
        payload = rubric_payloads[rubric_call_index["value"]]
        rubric_call_index["value"] += 1
        return payload

    provider = RecordingProviderAdapter(
        payloads=build_pipeline_provider_payloads(
            screening=screening,
            type_classification=type_classification,
            type_lens=build_type_lens_result(
                novel_type=type_classification.novelType,
                input_composition=screening.inputComposition,
                evaluation_mode=screening.evaluationMode,
            ),
            rubric_payload=provide_rubric_payload,
            aggregation_payload=aggregation.model_dump(mode="json"),
        )
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    result = pipeline.run(task=build_task(), submission=build_submission())

    assert len(result.projection.axes) == len(AxisId)
    assert result.projection.overall.score == 75
    assert result.projection.overall.verdict == aggregation.overallVerdictDraft
    assert result.projection.overall.platformCandidates == aggregation.platformCandidates
    assert result.typeClassification.novelType is NovelType.FANTASY_UPGRADE
    assert result.typeLens.novelType is NovelType.FANTASY_UPGRADE
    assert result.projection.typeAssessment is not None
    assert result.projection.typeAssessment.novelType is NovelType.FANTASY_UPGRADE
    assert len(result.projection.typeAssessment.lenses) == 4
    assert prompt_runtime.calls == [
        {
            "stage": "input_screening",
            "input_composition": "chapters_outline",
            "evaluation_mode": "full",
            "provider_id": "provider-test",
            "model_id": "model-test",
        },
        {
            "stage": "type_classification",
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
            "stage": "type_lens_evaluation",
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
    rubric_requests = [request for request in provider.requests if request.stage is StageName.RUBRIC_EVALUATION]
    assert len(rubric_requests) == 3
    assert [json.loads(request.messages[-1].content)["requestedAxes"] for request in rubric_requests] == [
        [axis_id.value for axis_id in batch] for batch in requested_axes_batches
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
            "stage": "type_classification",
            "timeoutMs": 90_000,
            "maxTokens": 2_500,
            "responseFormat": {"type": "json_object"},
        },
        {
            "stage": "rubric_evaluation",
            "timeoutMs": 90_000,
            "maxTokens": 6_000,
            "responseFormat": {"type": "json_object"},
        },
        {
            "stage": "rubric_evaluation",
            "timeoutMs": 90_000,
            "maxTokens": 6_000,
            "responseFormat": {"type": "json_object"},
        },
        {
            "stage": "rubric_evaluation",
            "timeoutMs": 90_000,
            "maxTokens": 6_000,
            "responseFormat": {"type": "json_object"},
        },
        {
            "stage": "type_lens_evaluation",
            "timeoutMs": 90_000,
            "maxTokens": 4_000,
            "responseFormat": {"type": "json_object"},
        },
        {
            "stage": "aggregation",
            "timeoutMs": 90_000,
            "maxTokens": 4_000,
            "responseFormat": {"type": "json_object"},
        },
    ]


def test_scoring_pipeline_blocks_when_any_rubric_slice_is_invalid() -> None:
    screening = build_screening_result()
    prompt_runtime = RecordingPromptRuntime()
    requested_axes_batches = [
        [AxisId.HOOK_RETENTION, AxisId.SERIAL_MOMENTUM, AxisId.CHARACTER_DRIVE],
        [AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF, AxisId.SETTING_DIFFERENTIATION],
        [AxisId.PLATFORM_FIT, AxisId.COMMERCIAL_POTENTIAL],
    ]
    rubric_payloads = [
        build_rubric_slice_payload(requested_axes=requested_axes_batches[0]),
        build_rubric_slice_payload(requested_axes=[AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF]),
        build_rubric_slice_payload(requested_axes=requested_axes_batches[2]),
    ]
    rubric_call_index = {"value": 0}

    def provide_rubric_payload(request: Any) -> dict[str, Any]:
        payload = rubric_payloads[rubric_call_index["value"]]
        rubric_call_index["value"] += 1
        return payload

    provider = RecordingProviderAdapter(
        payloads=build_pipeline_provider_payloads(
            screening=screening,
            rubric_payload=provide_rubric_payload,
        )
    )
    pipeline = ScoringPipeline(prompt_runtime=prompt_runtime, provider_adapter=provider)

    with pytest.raises(PipelineFailureError) as exc_info:
        pipeline.run(task=build_task(), submission=build_submission())

    assert exc_info.value.error_code is ErrorCode.STAGE_SCHEMA_INVALID
    assert "rubric_evaluation" in exc_info.value.message
