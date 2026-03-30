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
)

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
    ScoreBand.ONE.value: 35,
    ScoreBand.TWO.value: 55,
    ScoreBand.THREE.value: 75,
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
    if total_length >= 800 and continue_allowed:
        confidence = min(0.96, confidence + 0.04)

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
        "segmentationPlan": None,
        "confidence": confidence,
        "continueAllowed": continue_allowed,
    }


def _build_rubric_output(request: ProviderExecutionRequest, payload: dict[str, Any]) -> dict[str, Any]:
    chapters_text = "\n".join(str(item) for item in payload.get("chapters", []))
    outline_text = str(payload.get("outline") or "")
    screening = payload.get("screening") or {}
    degraded = screening.get("evaluationMode") == EvaluationMode.DEGRADED.value
    requested_axes = [
        axis_id
        for axis_id in AxisId
        if axis_id.value in {str(value) for value in payload.get("requestedAxes", [])}
    ]
    if not requested_axes:
        requested_axes = list(AxisId)
    items = []
    axis_summaries = []
    risk_tags: set[str] = set()
    for axis_id in requested_axes:
        score_band, reason = _score_axis(axis_id, chapters_text=chapters_text, outline_text=outline_text)
        degraded_by_input = degraded and axis_id in {
            AxisId.SERIAL_MOMENTUM,
            AxisId.PACING_PAYOFF,
            AxisId.PLATFORM_FIT,
        }
        item_risk_tags = [FatalRisk.INSUFFICIENT_MATERIAL.value] if degraded_by_input else []
        risk_tags.update(item_risk_tags)
        items.append(
            {
                "evaluationId": f"eval-{axis_id.value}",
                "axisId": axis_id.value,
                "scoreBand": score_band,
                "reason": reason,
                "evidenceRefs": [
                    {
                        "sourceType": EvidenceSourceType.CHAPTERS.value if chapters_text else EvidenceSourceType.OUTLINE.value,
                        "sourceSpan": {"chapterIndex": 0} if chapters_text else {"outlineRef": "全段"},
                        "excerpt": (chapters_text or outline_text or "deterministic fallback")[:120],
                        "observationType": "narrative_observation",
                        "evidenceNote": "deterministic fallback 生成的稳定证据。",
                        "confidence": 0.78 if not degraded_by_input else 0.52,
                    }
                ],
                "confidence": 0.8 if not degraded_by_input else 0.55,
                "riskTags": item_risk_tags,
                "blockingSignals": [],
                "affectedSkeletonDimensions": [],
                "degradedByInput": degraded_by_input,
            }
        )
        axis_summaries.append({"axisId": axis_id.value, "summary": f"{axis_id.value} 维度总结"})
    return {
        "taskId": request.taskId,
        "stage": request.stage.value,
        "schemaVersion": request.schemaVersion,
        "promptVersion": request.promptVersion,
        "rubricVersion": request.rubricVersion,
        "providerId": request.providerId,
        "modelId": request.modelId,
        "inputComposition": payload.get("inputComposition") or request.inputComposition.value,
        "evaluationMode": screening.get("evaluationMode") or request.evaluationMode.value,
        "requestedAxes": [axis_id.value for axis_id in requested_axes],
        "items": items,
        "axisSummaries": axis_summaries,
        "missingRequiredAxes": [],
        "riskTags": sorted(risk_tags),
        "overallConfidence": 0.8 if not degraded else 0.62,
    }


def _build_aggregation_output(request: ProviderExecutionRequest, payload: dict[str, Any]) -> dict[str, Any]:
    screening = payload.get("screening") or {}
    rubric = payload.get("rubric") or {}
    consistency = payload.get("consistency") or {}
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
    degraded = screening.get("evaluationMode") == EvaluationMode.DEGRADED.value
    return {
        "taskId": request.taskId,
        "stage": request.stage.value,
        "schemaVersion": request.schemaVersion,
        "promptVersion": request.promptVersion,
        "rubricVersion": request.rubricVersion,
        "providerId": request.providerId,
        "modelId": request.modelId,
        "overallVerdictDraft": "建议补全正文后再复核。" if degraded else "建议继续观察并进入样章复核。",
        "verdictSubQuote": "当前样本量偏少，市场承接判断需等待正文补全后再确认。" if degraded else f"题材气质与 {platform} 的核心读者预期较为贴合，但仍需观察长线兑现能力。",
        "overallSummaryDraft": "当前结果基于 degraded 材料，整体结论偏保守。" if degraded else "章节主线与市场抓手已形成初步可读的总体判断。",
        "platformCandidates": [{"name": platform, "weight": 100, "pitchQuote": f"题材卖点与 {platform} 主流读者偏好一致，具备明确承接空间。"}],
        "marketFitDraft": f"当前题材更贴合 {platform} 的用户预期。",
        "strengthCandidates": ["题材定位清晰", "主线冲突具备继续阅读抓手"],
        "weaknessCandidates": ["正文样本仍不足以完全验证长线兑现" if degraded else "平台承接仍需更多正文样本验证"],
        "riskTags": sorted(set(risk_tags)),
        "overallConfidence": max(0.24, round(float(rubric.get("overallConfidence", 0.8)) - (0.12 if degraded else 0.0), 2)),
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
        return ScoreBand.THREE.value, "设定具备基础辨识度，但仍需进一步强化差异化。"
    if axis_id is AxisId.PLATFORM_FIT:
        genre = _infer_genre(combined)
        if genre in {"romance", "urban", "scifi", "fantasy", "horror"}:
            return ScoreBand.THREE.value, "题材标签和平台预期大体匹配。"
        return ScoreBand.TWO.value, "平台适配信号仍不充分。"
    if any(token in combined for token in ("付费", "连载", "追读", "爆点", "爽点")):
        return ScoreBand.FOUR.value, "商业化信号较明确，具备继续观察价值。"
    return ScoreBand.THREE.value, "商业化潜力基础尚可，但仍需更多样本验证。"


def _infer_genre(text: str) -> str:
    for genre, keywords in _GENRE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return genre
    return "general"
