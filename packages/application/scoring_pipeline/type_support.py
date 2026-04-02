from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from packages.schemas.common.enums import NovelType
from packages.schemas.common.novel_types import get_novel_type_label, get_type_lens_definitions
from packages.schemas.stages.type_classification import TypeClassificationCandidate


TYPE_CLASSIFICATION_MIN_CONFIDENCE = 0.60
TYPE_CLASSIFICATION_MIN_MARGIN = 0.12


@dataclass(frozen=True, slots=True)
class TypeSelectionDecision:
    novel_type: NovelType
    classification_confidence: float
    fallback_used: bool


def select_final_novel_type(
    candidates: Sequence[TypeClassificationCandidate],
) -> TypeSelectionDecision:
    top1 = candidates[0]
    top2_confidence = candidates[1].confidence if len(candidates) > 1 else 0.0
    margin = top1.confidence - top2_confidence
    if top1.confidence >= TYPE_CLASSIFICATION_MIN_CONFIDENCE and margin >= TYPE_CLASSIFICATION_MIN_MARGIN:
        return TypeSelectionDecision(
            novel_type=top1.novelType,
            classification_confidence=top1.confidence,
            fallback_used=False,
        )
    return TypeSelectionDecision(
        novel_type=NovelType.GENERAL_FALLBACK,
        classification_confidence=top1.confidence,
        fallback_used=True,
    )


def build_type_classification_summary(
    *,
    selected_type: NovelType,
    candidates: Sequence[TypeClassificationCandidate],
    fallback_used: bool,
) -> str:
    top1 = candidates[0]
    top2 = candidates[1] if len(candidates) > 1 else None
    if fallback_used:
        second_label = get_novel_type_label(top2.novelType) if top2 is not None else "其他类型"
        return (
            f"题材信号在“{get_novel_type_label(top1.novelType)}”与“{second_label}”之间分散，"
            "当前未达到窄类型判定阈值，按通用兜底类型继续执行 lens。"
        )
    return (
        f"当前样本更接近“{get_novel_type_label(selected_type)}”，"
        "后续将按该类型的固定 lens 继续评估题材兑现。"
    )


def build_type_lens_summary(*, novel_type: NovelType) -> str:
    lens_labels = " / ".join(definition.label for definition in get_type_lens_definitions(novel_type))
    return f"本次类型评价按“{get_novel_type_label(novel_type)}”lens 执行，重点观察：{lens_labels}。"
