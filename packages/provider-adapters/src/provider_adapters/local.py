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
    NovelType,
    ScoreBand,
    SkeletonDimensionId,
    StageName,
    StageStatus,
    Sufficiency,
)
from packages.schemas.common.novel_types import get_novel_type_label, get_type_lens_definitions

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

_NOVEL_TYPE_KEYWORDS = {
    NovelType.FEMALE_GENERAL: ("夫人", "王爷", "侯府", "嫡女", "替嫁", "和离", "先婚后爱", "世子", "婚约", "姨娘"),
    NovelType.FANTASY_UPGRADE: ("修仙", "宗门", "灵气", "系统", "升级", "面板", "异能", "秘境", "大阵", "炼丹"),
    NovelType.URBAN_REALITY: ("都市", "职场", "公司", "商战", "神豪", "创业", "经营", "董事会", "地产", "资本"),
    NovelType.HISTORY_MILITARY: ("历史", "朝堂", "边关", "将军", "军队", "皇帝", "王朝", "战争", "谋臣", "争霸"),
    NovelType.SCI_FI_APOCALYPSE: ("星际", "机甲", "赛博", "末世", "宇宙", "舰队", "虫族", "基地", "废土", "跃迁"),
    NovelType.SUSPENSE_HORROR: ("悬疑", "推理", "刑侦", "规则怪谈", "惊悚", "诡异", "凶案", "谜题", "线索", "怪谈"),
    NovelType.GAME_DERIVATIVE: ("副本", "无限流", "游戏", "电竞", "同人", "诸天", "穿梭", "轮回", "build", "关卡"),
}
_FALLBACK_TYPE_ORDER = (
    NovelType.URBAN_REALITY,
    NovelType.FANTASY_UPGRADE,
    NovelType.GAME_DERIVATIVE,
    NovelType.HISTORY_MILITARY,
    NovelType.SCI_FI_APOCALYPSE,
    NovelType.SUSPENSE_HORROR,
    NovelType.FEMALE_GENERAL,
    NovelType.GENERAL_FALLBACK,
)


def _build_structured_stage_output(request: ProviderExecutionRequest) -> dict[str, Any]:
    payload = _load_payload(request)
    if request.stage is StageName.INPUT_SCREENING:
        return _build_screening_output(request, payload)
    if request.stage is StageName.TYPE_CLASSIFICATION:
        return _build_type_classification_output(request, payload)
    if request.stage is StageName.RUBRIC_EVALUATION:
        return _build_rubric_output(request, payload)
    if request.stage is StageName.TYPE_LENS_EVALUATION:
        return _build_type_lens_output(request, payload)
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
    type_classification = payload.get("typeClassification") or {}
    rubric = payload.get("rubric") or {}
    type_lens = payload.get("typeLens") or {}
    consistency = payload.get("consistency") or {}
    chapters_text = "\n".join(str(item) for item in payload.get("chapters", []))
    outline_text = str(payload.get("outline") or "")
    novel_type = _resolve_novel_type(type_classification.get("novelType")) or _infer_novel_type(f"{chapters_text}\n{outline_text}")
    platform = _platform_for_novel_type(novel_type)
    risk_tags = sorted(set(rubric.get("riskTags", [])))
    if not consistency.get("passed", True):
        risk_tags.append(FatalRisk.FAKE_PAYOFF.value)
    degraded = screening.get("evaluationMode") == EvaluationMode.DEGRADED.value
    type_summary = str(type_lens.get("summary") or f"当前按 {get_novel_type_label(novel_type)} lens 继续评估。").strip()
    return {
        "taskId": request.taskId,
        "stage": request.stage.value,
        "schemaVersion": request.schemaVersion,
        "promptVersion": request.promptVersion,
        "rubricVersion": request.rubricVersion,
        "providerId": request.providerId,
        "modelId": request.modelId,
        "overallVerdictDraft": "建议补全正文后再复核。" if degraded else "建议继续观察并进入样章复核。",
        "verdictSubQuote": (
            "当前样本量偏少，市场承接判断需等待正文补全后再确认。"
            if degraded
            else f"作品当前归入{get_novel_type_label(novel_type)}，与 {platform} 的圈层预期更为贴合。"
        ),
        "overallSummaryDraft": (
            f"当前结果基于 degraded 材料，整体结论偏保守；类型评估暂按 {get_novel_type_label(novel_type)} lens 处理。"
            if degraded
            else f"章节主线与市场抓手已形成初步可读的总体判断；{type_summary}"
        ),
        "platformCandidates": [{"name": platform, "weight": 100, "pitchQuote": f"题材卖点与 {platform} 主流读者偏好一致，具备明确承接空间。"}],
        "marketFitDraft": f"当前作品被识别为 {get_novel_type_label(novel_type)}，更贴合 {platform} 的用户预期。",
        "strengthCandidates": ["题材定位清晰", "主线冲突具备继续阅读抓手"],
        "weaknessCandidates": ["正文样本仍不足以完全验证长线兑现" if degraded else "平台承接仍需更多正文样本验证"],
        "riskTags": sorted(set(risk_tags)),
        "overallConfidence": max(0.24, round(float(rubric.get("overallConfidence", 0.8)) - (0.12 if degraded else 0.0), 2)),
    }


def _build_type_classification_output(request: ProviderExecutionRequest, payload: dict[str, Any]) -> dict[str, Any]:
    chapters_text = "\n".join(str(item) for item in payload.get("chapters", []))
    outline_text = str(payload.get("outline") or "")
    combined_text = f"{chapters_text}\n{outline_text}"
    candidates = _rank_novel_types(combined_text)
    top_label = get_novel_type_label(_resolve_novel_type(candidates[0]["novelType"]) or NovelType.GENERAL_FALLBACK)
    second_label = get_novel_type_label(_resolve_novel_type(candidates[1]["novelType"]) or NovelType.GENERAL_FALLBACK)
    return {
        "taskId": request.taskId,
        "stage": request.stage.value,
        "schemaVersion": request.schemaVersion,
        "promptVersion": request.promptVersion,
        "rubricVersion": request.rubricVersion,
        "providerId": request.providerId,
        "modelId": request.modelId,
        "inputComposition": payload.get("inputComposition") or request.inputComposition.value,
        "evaluationMode": payload.get("evaluationMode") or request.evaluationMode.value,
        "candidates": candidates,
        "summary": f"当前最高题材信号落在“{top_label}”，次高候选为“{second_label}”。",
    }


def _build_type_lens_output(request: ProviderExecutionRequest, payload: dict[str, Any]) -> dict[str, Any]:
    chapters_text = "\n".join(str(item) for item in payload.get("chapters", []))
    outline_text = str(payload.get("outline") or "")
    combined_text = f"{chapters_text}\n{outline_text}"
    selected_type = _resolve_novel_type((payload.get("selectedType") or {}).get("novelType")) or NovelType.GENERAL_FALLBACK
    degraded = (payload.get("screening") or {}).get("evaluationMode") == EvaluationMode.DEGRADED.value
    items = [
        _build_type_lens_item(
            novel_type=selected_type,
            lens_id=definition.lens_id,
            label=definition.label,
            combined_text=combined_text,
            degraded=degraded,
        )
        for definition in get_type_lens_definitions(selected_type)
    ]
    return {
        "taskId": request.taskId,
        "stage": request.stage.value,
        "schemaVersion": request.schemaVersion,
        "promptVersion": request.promptVersion,
        "rubricVersion": request.rubricVersion,
        "providerId": request.providerId,
        "modelId": request.modelId,
        "inputComposition": payload.get("inputComposition") or request.inputComposition.value,
        "evaluationMode": payload.get("evaluationMode") or request.evaluationMode.value,
        "novelType": selected_type.value,
        "summary": f"本次类型评价按“{get_novel_type_label(selected_type)}”lens 执行。",
        "items": items,
        "overallConfidence": min(item["confidence"] for item in items),
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
        novel_type = _infer_novel_type(combined)
        if novel_type is not NovelType.GENERAL_FALLBACK:
            return ScoreBand.THREE.value, "题材标签和平台预期大体匹配。"
        return ScoreBand.TWO.value, "平台适配信号仍不充分。"
    if any(token in combined for token in ("付费", "连载", "追读", "爆点", "爽点")):
        return ScoreBand.FOUR.value, "商业化信号较明确，具备继续观察价值。"
    return ScoreBand.THREE.value, "商业化潜力基础尚可，但仍需更多样本验证。"


def _rank_novel_types(text: str) -> list[dict[str, Any]]:
    scores = {
        novel_type: _count_keywords(text, keywords)
        for novel_type, keywords in _NOVEL_TYPE_KEYWORDS.items()
    }
    ranked = sorted(
        scores.items(),
        key=lambda item: (item[1], item[0].value != NovelType.FEMALE_GENERAL.value),
        reverse=True,
    )
    if ranked[0][1] == 0:
        base_candidates = [
            NovelType.GENERAL_FALLBACK,
            NovelType.URBAN_REALITY,
            NovelType.FANTASY_UPGRADE,
        ]
        return [
            {
                "novelType": novel_type.value,
                "confidence": confidence,
                "reason": "当前样本缺少稳定题材关键词，需保守处理类型判断。",
            }
            for novel_type, confidence in zip(base_candidates, (0.46, 0.38, 0.31), strict=True)
        ]
    top_types = [novel_type for novel_type, _score in ranked[:3]]
    while len(top_types) < 3:
        for fallback_type in _FALLBACK_TYPE_ORDER:
            if fallback_type not in top_types:
                top_types.append(fallback_type)
            if len(top_types) == 3:
                break
    top_score = max(scores.values())
    second_score = scores.get(top_types[1], 0)
    mixed_signal = top_score > 0 and second_score >= top_score - 1
    candidates: list[dict[str, Any]] = []
    for index, novel_type in enumerate(top_types[:3]):
        raw_score = scores.get(novel_type, 0)
        confidence = 0.38 + raw_score * 0.09 - index * 0.07
        if novel_type is NovelType.FEMALE_GENERAL and raw_score >= 2:
            confidence += 0.06
        if mixed_signal and index == 0:
            confidence -= 0.12
        confidence = round(max(0.18, min(0.92, confidence)), 2)
        candidates.append(
            {
                "novelType": novel_type.value,
                "confidence": confidence,
                "reason": f"样本中出现了较多“{get_novel_type_label(novel_type)}”信号。",
            }
        )
    return candidates


def _build_type_lens_item(
    *,
    novel_type: NovelType,
    lens_id: str,
    label: str,
    combined_text: str,
    degraded: bool,
) -> dict[str, Any]:
    matching_keywords = _count_keywords(combined_text, _NOVEL_TYPE_KEYWORDS.get(novel_type, ()))
    score_band = ScoreBand.THREE.value if matching_keywords >= 2 else ScoreBand.TWO.value
    if matching_keywords >= 4:
        score_band = ScoreBand.FOUR.value
    confidence = 0.58 if degraded else 0.78
    if score_band == ScoreBand.FOUR.value:
        confidence += 0.05
    return {
        "lensId": lens_id,
        "label": label,
        "scoreBand": score_band,
        "reason": f"{label} 当前具备可判断的题材兑现信号，但仍需后续连载继续验证。",
        "evidenceRefs": [
            {
                "sourceType": EvidenceSourceType.CHAPTERS.value if combined_text.strip() else EvidenceSourceType.OUTLINE.value,
                "sourceSpan": {"chapterIndex": 0} if combined_text.strip() else {"outlineRef": "全段"},
                "excerpt": (combined_text or "deterministic type lens fallback")[:120],
                "observationType": "narrative_observation",
                "evidenceNote": "deterministic type lens 输出的稳定证据。",
                "confidence": round(confidence - 0.04, 2),
            }
        ],
        "confidence": round(confidence, 2),
        "riskTags": [FatalRisk.INSUFFICIENT_MATERIAL.value] if degraded else [],
        "degradedByInput": degraded,
    }


def _count_keywords(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def _infer_novel_type(text: str) -> NovelType:
    return _resolve_novel_type(_rank_novel_types(text)[0]["novelType"]) or NovelType.GENERAL_FALLBACK


def _resolve_novel_type(raw_value: Any) -> NovelType | None:
    if isinstance(raw_value, NovelType):
        return raw_value
    if not isinstance(raw_value, str):
        return None
    stripped = raw_value.strip()
    for novel_type in NovelType:
        if stripped == novel_type.value:
            return novel_type
    return None


def _platform_for_novel_type(novel_type: NovelType) -> str:
    return {
        NovelType.FEMALE_GENERAL: "女频平台 A",
        NovelType.FANTASY_UPGRADE: "玄幻平台 D",
        NovelType.URBAN_REALITY: "都市平台 B",
        NovelType.HISTORY_MILITARY: "历史平台 C",
        NovelType.SCI_FI_APOCALYPSE: "科幻平台 C",
        NovelType.SUSPENSE_HORROR: "悬疑平台 E",
        NovelType.GAME_DERIVATIVE: "游戏平台 F",
        NovelType.GENERAL_FALLBACK: "综合平台 A",
    }[novel_type]
