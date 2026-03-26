from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from packages.schemas.common.enums import (
    AxisId,
    EvaluationMode,
    EvidenceSourceType,
    FatalRisk,
    InputComposition,
    ScoreBand,
    SkeletonDimensionId,
    StageName,
    StageStatus,
    Sufficiency,
    TopLevelScoreField,
)
from packages.schemas.output.result import DetailedAnalysis

from .contracts import (
    ProviderExecutionFailure,
    ProviderExecutionRequest,
    ProviderExecutionResult,
    ProviderExecutionSuccess,
    ProviderFailureType,
    build_provider_failure,
)


class LocalAdapterMode(StrEnum):
    SUCCESS = "success"
    PROVIDER_FAILURE = ProviderFailureType.PROVIDER_FAILURE.value
    TIMEOUT = ProviderFailureType.TIMEOUT.value
    DEPENDENCY_UNAVAILABLE = ProviderFailureType.DEPENDENCY_UNAVAILABLE.value
    CONTRACT_INVALID = ProviderFailureType.CONTRACT_INVALID.value


@dataclass(frozen=True, slots=True)
class LocalDeterministicProviderAdapter:
    provider_id: str = "provider-local"
    model_id: str = "model-local"
    mode: LocalAdapterMode = LocalAdapterMode.SUCCESS
    duration_ms: int = 5
    provider_failure_retryable: bool | None = None
    structured_stage_outputs: bool = False

    def execute(self, request: ProviderExecutionRequest) -> ProviderExecutionResult:
        if request.providerId != self.provider_id or request.modelId != self.model_id:
            return build_provider_failure(
                provider_id=self.provider_id,
                model_id=self.model_id,
                request_id=request.requestId,
                provider_request_id=None,
                duration_ms=self.duration_ms,
                failure_type=ProviderFailureType.CONTRACT_INVALID,
                message="本地 deterministic adapter 收到与自身不匹配的 providerId 或 modelId。",
            )
        if self.mode is LocalAdapterMode.SUCCESS:
            return self._build_success(request)

        failure_type = ProviderFailureType(self.mode.value)
        provider_request_id = self._build_provider_request_id(request)
        if failure_type in {
            ProviderFailureType.DEPENDENCY_UNAVAILABLE,
            ProviderFailureType.CONTRACT_INVALID,
        }:
            provider_request_id = None

        return self._build_failure(
            request=request,
            failure_type=failure_type,
            provider_request_id=provider_request_id,
            message=self._build_failure_message(failure_type),
        )

    def _build_success(self, request: ProviderExecutionRequest) -> ProviderExecutionSuccess:
        provider_request_id = self._build_provider_request_id(request)
        raw_json = (
            _build_structured_stage_output(request)
            if self.structured_stage_outputs
            else {
                "adapter": "local_deterministic",
                "taskId": request.taskId,
                "stage": request.stage.value,
                "messageCount": len(request.messages),
                "messages": [
                    {"role": message.role, "content": message.content}
                    for message in request.messages
                ],
            }
        )
        raw_text = json.dumps(raw_json, ensure_ascii=False, sort_keys=True)
        return ProviderExecutionSuccess(
            providerId=self.provider_id,
            modelId=self.model_id,
            requestId=request.requestId,
            providerRequestId=provider_request_id,
            durationMs=self.duration_ms,
            rawText=raw_text,
            rawJson=raw_json,
        )

    def _build_failure(
        self,
        *,
        request: ProviderExecutionRequest,
        failure_type: ProviderFailureType,
        provider_request_id: str | None,
        message: str,
    ) -> ProviderExecutionFailure:
        retryable = self.provider_failure_retryable if failure_type is ProviderFailureType.PROVIDER_FAILURE else None
        return build_provider_failure(
            provider_id=self.provider_id,
            model_id=self.model_id,
            request_id=request.requestId,
            provider_request_id=provider_request_id,
            duration_ms=self.duration_ms,
            failure_type=failure_type,
            message=message,
            retryable=retryable,
        )

    def _build_provider_request_id(self, request: ProviderExecutionRequest) -> str:
        return f"local-{request.requestId}"

    def _build_failure_message(self, failure_type: ProviderFailureType) -> str:
        if failure_type is ProviderFailureType.PROVIDER_FAILURE:
            return "本地 deterministic adapter 模拟 provider_failure。"
        if failure_type is ProviderFailureType.TIMEOUT:
            return "本地 deterministic adapter 模拟 timeout。"
        if failure_type is ProviderFailureType.DEPENDENCY_UNAVAILABLE:
            return "本地 deterministic adapter 模拟 dependency_unavailable。"
        return "本地 deterministic adapter 模拟 contract_invalid。"


_SCORE_BAND_TO_PERCENT = {
    ScoreBand.ZERO.value: 20,
    ScoreBand.ONE.value: 38,
    ScoreBand.TWO.value: 56,
    ScoreBand.THREE.value: 76,
    ScoreBand.FOUR.value: 90,
}

_GENRE_KEYWORDS = {
    "urban": ("都市", "总裁", "豪门", "职场"),
    "scifi": ("星际", "机甲", "宇宙", "赛博"),
    "fantasy": ("修仙", "宗门", "仙门", "灵气"),
    "horror": ("规则怪谈", "诡异", "惊悚"),
    "romance": ("恋爱", "婚约", "感情"),
}


def _build_structured_stage_output(request: ProviderExecutionRequest) -> dict[str, Any]:
    payload = _load_payload(request)
    if request.stage is StageName.INPUT_SCREENING:
        return _build_screening_output(request, payload)
    if request.stage is StageName.RUBRIC_EVALUATION:
        return _build_rubric_output(request, payload)
    if request.stage is StageName.AGGREGATION:
        return _build_aggregation_output(request, payload)
    raise ValueError(f"不支持的 structured stage: {request.stage}")


def _load_payload(request: ProviderExecutionRequest) -> dict[str, Any]:
    for message in reversed(request.messages):
        if message.role != "user":
            continue
        try:
            parsed = json.loads(message.content)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _build_screening_output(request: ProviderExecutionRequest, payload: dict[str, Any]) -> dict[str, Any]:
    chapters = [str(item) for item in payload.get("chapters", [])]
    chapters_text = "\n".join(chapters).strip()
    outline_text = str(payload.get("outline") or "").strip()
    input_composition = str(payload.get("inputComposition") or request.inputComposition.value)
    has_chapters = bool(chapters_text)
    has_outline = bool(outline_text)
    chapters_sufficiency = _classify_sufficiency(chapters_text, threshold=4)
    outline_sufficiency = _classify_sufficiency(outline_text, threshold=4)
    non_narrative = any(token in f"{chapters_text}\n{outline_text}" for token in ("简历", "说明书", "API 文档", "合同", "非小说"))

    if non_narrative:
        evaluation_mode = request.evaluationMode.value
        rateable = False
        continue_allowed = False
        status = StageStatus.UNRATEABLE.value
        rejection_reasons = ["输入文本不具备小说叙事特征，无法进入正式评分。"]
        risk_tags = [FatalRisk.NON_NARRATIVE_SUBMISSION.value]
        confidence = 0.18
    else:
        sufficient_sides = sum(
            sufficiency == Sufficiency.SUFFICIENT.value
            for sufficiency in (chapters_sufficiency, outline_sufficiency)
        )
        rateable = sufficient_sides >= 1
        continue_allowed = rateable
        evaluation_mode = (
            EvaluationMode.FULL.value
            if input_composition == InputComposition.CHAPTERS_OUTLINE.value
            and chapters_sufficiency == Sufficiency.SUFFICIENT.value
            and outline_sufficiency == Sufficiency.SUFFICIENT.value
            else EvaluationMode.DEGRADED.value
        )
        status = StageStatus.OK.value if evaluation_mode == EvaluationMode.FULL.value else (
            StageStatus.WARNING.value if continue_allowed else StageStatus.UNRATEABLE.value
        )
        rejection_reasons = [] if continue_allowed else ["输入材料不足，无法形成稳定评分结论。"]
        risk_tags = [] if continue_allowed and evaluation_mode == EvaluationMode.FULL.value else [FatalRisk.INSUFFICIENT_MATERIAL.value]
        confidence = 0.9 if evaluation_mode == EvaluationMode.FULL.value else (0.72 if continue_allowed else 0.24)

    total_length = len(chapters_text) + len(outline_text)
    segmentation_plan = {
        "strategy": "single_pass" if total_length < 1800 else "chunked",
        "segments": [{"segmentId": "segment_001", "length": total_length}],
        "overflowPolicy": "truncate_tail" if total_length > 4000 else "none",
        "truncated": total_length > 4000,
    }

    return {
        "taskId": request.taskId,
        "stage": request.stage.value,
        "schemaVersion": request.schemaVersion,
        "promptVersion": request.promptVersion,
        "rubricVersion": request.rubricVersion,
        "providerId": request.providerId,
        "modelId": request.modelId,
        "inputComposition": input_composition,
        "hasChapters": has_chapters,
        "hasOutline": has_outline,
        "chaptersSufficiency": chapters_sufficiency,
        "outlineSufficiency": outline_sufficiency,
        "evaluationMode": evaluation_mode,
        "rateable": rateable,
        "status": status,
        "rejectionReasons": rejection_reasons,
        "riskTags": risk_tags,
        "segmentationPlan": segmentation_plan,
        "confidence": confidence,
        "continueAllowed": continue_allowed,
    }


def _build_rubric_output(request: ProviderExecutionRequest, payload: dict[str, Any]) -> dict[str, Any]:
    chapters_text = "\n".join(str(item) for item in payload.get("chapters", [])).strip()
    outline_text = str(payload.get("outline") or "").strip()
    screening = payload.get("screening", {})
    evaluation_mode = str(payload.get("evaluationMode") or screening.get("evaluationMode") or request.evaluationMode.value)
    input_composition = str(payload.get("inputComposition") or screening.get("inputComposition") or request.inputComposition.value)
    degraded = evaluation_mode == EvaluationMode.DEGRADED.value
    risk_tags: set[str] = set()
    axis_summaries: dict[str, str] = {}
    items: list[dict[str, Any]] = []

    for index, axis_id in enumerate(AxisId, start=1):
        score_band, reason = _score_axis(axis_id, chapters_text=chapters_text, outline_text=outline_text)
        confidence = max(0.22, 0.84 - (0.12 if degraded else 0.0) - ((4 - int(score_band)) * 0.04))
        item_risk_tags = [FatalRisk.INSUFFICIENT_MATERIAL.value] if degraded else []
        if "模板" in chapters_text or "套路" in outline_text:
            item_risk_tags.append(FatalRisk.STALE_FORMULA.value)
        risk_tags.update(item_risk_tags)
        items.append(
            {
                "evaluationId": f"{request.taskId}_{axis_id.value}_{index:02d}",
                "axisId": axis_id.value,
                "scoreBand": score_band,
                "reason": reason,
                "evidenceRefs": [
                    {
                        "sourceType": _select_evidence_source(axis_id, chapters_text, outline_text),
                        "sourceSpan": {"offset": 0, "length": min(80, len(chapters_text or outline_text))},
                        "excerpt": _build_excerpt(axis_id, chapters_text, outline_text),
                        "observationType": "deterministic_signal",
                        "evidenceNote": reason,
                        "confidence": confidence,
                    }
                ],
                "confidence": confidence,
                "riskTags": item_risk_tags,
                "blockingSignals": [],
                "affectedSkeletonDimensions": _map_axis_to_skeleton(axis_id),
                "degradedByInput": degraded,
            }
        )
        axis_summaries[axis_id.value] = reason

    overall_confidence = max(0.2, sum(item["confidence"] for item in items) / len(items))
    return {
        "taskId": request.taskId,
        "stage": request.stage.value,
        "schemaVersion": request.schemaVersion,
        "promptVersion": request.promptVersion,
        "rubricVersion": request.rubricVersion,
        "providerId": request.providerId,
        "modelId": request.modelId,
        "inputComposition": input_composition,
        "evaluationMode": evaluation_mode,
        "items": items,
        "axisSummaries": axis_summaries,
        "missingRequiredAxes": [],
        "riskTags": sorted(risk_tags),
        "overallConfidence": overall_confidence,
    }


def _build_aggregation_output(request: ProviderExecutionRequest, payload: dict[str, Any]) -> dict[str, Any]:
    screening = payload.get("screening", {})
    rubric = payload.get("rubric", {})
    consistency = payload.get("consistency", {})
    item_map = {
        item["axisId"]: _SCORE_BAND_TO_PERCENT[item["scoreBand"]]
        for item in rubric.get("items", [])
    }
    axis_scores = {axis.value: item_map[axis.value] for axis in AxisId}
    skeleton_scores = {
        SkeletonDimensionId.MARKET_ATTRACTION.value: _average(
            axis_scores[AxisId.HOOK_RETENTION.value],
            axis_scores[AxisId.SERIAL_MOMENTUM.value],
            axis_scores[AxisId.PLATFORM_FIT.value],
            axis_scores[AxisId.COMMERCIAL_POTENTIAL.value],
        ),
        SkeletonDimensionId.NARRATIVE_EXECUTION.value: _average(
            axis_scores[AxisId.NARRATIVE_CONTROL.value],
            axis_scores[AxisId.PACING_PAYOFF.value],
        ),
        SkeletonDimensionId.CHARACTER_MOMENTUM.value: _average(
            axis_scores[AxisId.CHARACTER_DRIVE.value],
            axis_scores[AxisId.SERIAL_MOMENTUM.value],
        ),
        SkeletonDimensionId.NOVELTY_UTILITY.value: _average(
            axis_scores[AxisId.SETTING_DIFFERENTIATION.value],
            axis_scores[AxisId.PLATFORM_FIT.value],
        ),
    }
    top_level_scores = {
        TopLevelScoreField.SIGNING_PROBABILITY.value: _average(
            skeleton_scores[SkeletonDimensionId.MARKET_ATTRACTION.value],
            skeleton_scores[SkeletonDimensionId.NARRATIVE_EXECUTION.value],
            axis_scores[AxisId.PLATFORM_FIT.value],
        ),
        TopLevelScoreField.COMMERCIAL_VALUE.value: _average(
            skeleton_scores[SkeletonDimensionId.MARKET_ATTRACTION.value],
            skeleton_scores[SkeletonDimensionId.CHARACTER_MOMENTUM.value],
        ),
        TopLevelScoreField.WRITING_QUALITY.value: _average(
            skeleton_scores[SkeletonDimensionId.NARRATIVE_EXECUTION.value],
            axis_scores[AxisId.NARRATIVE_CONTROL.value],
        ),
        TopLevelScoreField.INNOVATION_SCORE.value: _average(
            skeleton_scores[SkeletonDimensionId.NOVELTY_UTILITY.value],
            axis_scores[AxisId.SETTING_DIFFERENTIATION.value],
        ),
    }
    chapters_text = "\n".join(str(item) for item in payload.get("chapters", []))
    outline_text = str(payload.get("outline") or "")
    genre = _infer_genre(f"{chapters_text}\n{outline_text}")
    platform = {
        "romance": "女频平台 A",
        "urban": "都市平台 B",
        "scifi": "男频平台 C",
        "fantasy": "幻想平台 D",
        "horror": "悬疑平台 E",
    }.get(genre, "综合平台 A")
    risk_tags = sorted(set(rubric.get("riskTags", [])))
    if not consistency.get("passed", True):
        risk_tags.append(FatalRisk.FAKE_PAYOFF.value)
    strengths = _top_axes(axis_scores, reverse=True)
    weaknesses = _top_axes(axis_scores, reverse=False)
    confidence_penalty = 0.12 if screening.get("evaluationMode") == EvaluationMode.DEGRADED.value else 0.0
    confidence_penalty += 0.18 if not consistency.get("passed", True) else 0.0

    return {
        "taskId": request.taskId,
        "stage": request.stage.value,
        "schemaVersion": request.schemaVersion,
        "promptVersion": request.promptVersion,
        "rubricVersion": request.rubricVersion,
        "providerId": request.providerId,
        "modelId": request.modelId,
        "axisScores": axis_scores,
        "skeletonScores": skeleton_scores,
        "topLevelScoresDraft": top_level_scores,
        "strengthCandidates": [f"{axis} 维度表现较强" for axis in strengths],
        "weaknessCandidates": [f"{axis} 维度仍需补强" for axis in weaknesses],
        "platformCandidates": [platform],
        "marketFitDraft": f"当前题材更贴合 {platform} 的用户预期。",
        "editorVerdictDraft": "建议继续观察并进入样章复核。",
        "detailedAnalysisDraft": DetailedAnalysis(
            plot="章节主线已具备基础推进力。",
            character="角色驱动存在明确行动目标。",
            pacing="节奏兑现依赖后续章节补强。",
            worldBuilding="设定卖点已形成初步差异化。",
        ).model_dump(mode="json"),
        "supportingAxisMap": {
            TopLevelScoreField.SIGNING_PROBABILITY.value: [
                AxisId.COMMERCIAL_POTENTIAL.value,
                AxisId.PLATFORM_FIT.value,
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
        },
        "supportingSkeletonMap": {
            TopLevelScoreField.SIGNING_PROBABILITY.value: [SkeletonDimensionId.MARKET_ATTRACTION.value],
            TopLevelScoreField.COMMERCIAL_VALUE.value: [
                SkeletonDimensionId.MARKET_ATTRACTION.value,
                SkeletonDimensionId.CHARACTER_MOMENTUM.value,
            ],
            TopLevelScoreField.WRITING_QUALITY.value: [SkeletonDimensionId.NARRATIVE_EXECUTION.value],
            TopLevelScoreField.INNOVATION_SCORE.value: [SkeletonDimensionId.NOVELTY_UTILITY.value],
        },
        "riskTags": sorted(set(risk_tags)),
        "overallConfidence": max(0.24, round(rubric.get("overallConfidence", 0.8) - confidence_penalty, 2)),
    }


def _classify_sufficiency(text: str, *, threshold: int) -> str:
    normalized = text.strip()
    if not normalized:
        return Sufficiency.MISSING.value
    if len(normalized) >= threshold:
        return Sufficiency.SUFFICIENT.value
    return Sufficiency.INSUFFICIENT.value


def _score_axis(axis_id: AxisId, *, chapters_text: str, outline_text: str) -> tuple[str, str]:
    combined = f"{chapters_text}\n{outline_text}"
    if axis_id is AxisId.HOOK_RETENTION:
        if any(token in chapters_text for token in ("悬念", "危机", "秘密", "冲突")):
            return ScoreBand.FOUR.value, "开篇直接给出冲突或悬念，读者留存信号较强。"
        if len(chapters_text) > 140:
            return ScoreBand.THREE.value, "开篇信息量充足，但钩子力度仍可继续强化。"
        return ScoreBand.TWO.value, "开篇素材有限，留存抓手尚不稳定。"
    if axis_id is AxisId.SERIAL_MOMENTUM:
        if any(token in outline_text for token in ("主线", "升级", "连载", "阶段目标")):
            return ScoreBand.FOUR.value, "大纲给出了清晰的连载推进目标。"
        if outline_text:
            return ScoreBand.THREE.value, "大纲存在后续方向，但持续推进力一般。"
        return ScoreBand.TWO.value, "缺少稳定的大纲支撑，连载惯性判断偏弱。"
    if axis_id is AxisId.CHARACTER_DRIVE:
        if any(token in chapters_text for token in ("想要", "必须", "决定", "目标")):
            return ScoreBand.FOUR.value, "角色目标和行动驱动力表达清晰。"
        return (ScoreBand.THREE.value, "角色行为动机基本成立。") if chapters_text else (ScoreBand.TWO.value, "角色驱动证据偏少。")
    if axis_id is AxisId.NARRATIVE_CONTROL:
        return (ScoreBand.FOUR.value, "叙事层次与信息组织较稳。") if len(chapters_text) > 220 else (ScoreBand.THREE.value, "叙事基本可读，但控制力仍有提升空间。")
    if axis_id is AxisId.PACING_PAYOFF:
        if any(token in combined for token in ("伏笔", "回收", "兑现")):
            return ScoreBand.FOUR.value, "节奏与兑现存在明确对应关系。"
        return (ScoreBand.THREE.value, "节奏推进基本顺畅。") if chapters_text and outline_text else (ScoreBand.TWO.value, "节奏兑现需要更多样本支持。")
    if axis_id is AxisId.SETTING_DIFFERENTIATION:
        if any(token in combined for token in ("星际", "赛博", "规则怪谈", "修仙", "末世")):
            return ScoreBand.FOUR.value, "题材与设定具备清晰差异化卖点。"
        return ScoreBand.THREE.value, "设定基础明确，但差异化程度中等。"
    if axis_id is AxisId.PLATFORM_FIT:
        genre = _infer_genre(combined)
        return (
            (ScoreBand.FOUR.value, f"题材标签清晰，平台适配方向稳定。")
            if genre is not None
            else (ScoreBand.TWO.value, "平台适配信号不够明确。")
        )
    if any(token in combined for token in ("付费", "订阅", "签约", "爆点", "追更")):
        return ScoreBand.FOUR.value, "商业化抓手明确，具备较强转化潜力。"
    return ScoreBand.THREE.value, "商业潜力存在，但仍依赖后续兑现。"


def _select_evidence_source(axis_id: AxisId, chapters_text: str, outline_text: str) -> str:
    if axis_id in {AxisId.HOOK_RETENTION, AxisId.CHARACTER_DRIVE, AxisId.NARRATIVE_CONTROL}:
        return EvidenceSourceType.CHAPTERS.value
    if axis_id in {AxisId.SERIAL_MOMENTUM} and outline_text:
        return EvidenceSourceType.OUTLINE.value
    if chapters_text and outline_text:
        return EvidenceSourceType.CROSS_INPUT.value
    return EvidenceSourceType.CHAPTERS.value if chapters_text else EvidenceSourceType.OUTLINE.value


def _build_excerpt(axis_id: AxisId, chapters_text: str, outline_text: str) -> str:
    source = outline_text if axis_id is AxisId.SERIAL_MOMENTUM and outline_text else (chapters_text or outline_text)
    normalized = source.strip()
    return normalized[:80] if normalized else "样本为空，使用 deterministic fallback。"


def _map_axis_to_skeleton(axis_id: AxisId) -> list[str]:
    if axis_id in {AxisId.HOOK_RETENTION, AxisId.SERIAL_MOMENTUM, AxisId.PLATFORM_FIT, AxisId.COMMERCIAL_POTENTIAL}:
        return [SkeletonDimensionId.MARKET_ATTRACTION.value]
    if axis_id in {AxisId.NARRATIVE_CONTROL, AxisId.PACING_PAYOFF}:
        return [SkeletonDimensionId.NARRATIVE_EXECUTION.value]
    if axis_id is AxisId.CHARACTER_DRIVE:
        return [SkeletonDimensionId.CHARACTER_MOMENTUM.value]
    return [SkeletonDimensionId.NOVELTY_UTILITY.value]


def _average(*values: int) -> int:
    return round(sum(values) / len(values))


def _top_axes(axis_scores: dict[str, int], *, reverse: bool) -> list[str]:
    ordered = sorted(axis_scores.items(), key=lambda item: item[1], reverse=reverse)
    return [axis_id for axis_id, _ in ordered[:2]]


def _infer_genre(text: str) -> str | None:
    normalized = text.strip()
    if not normalized:
        return None
    for genre, keywords in _GENRE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return genre
    return None
