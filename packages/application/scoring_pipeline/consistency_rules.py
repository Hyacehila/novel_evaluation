from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class ConsistencyThresholds:
    weak_evidence_confidence: float = 0.3
    unsupported_claim_evidence_confidence: float = 0.55
    duplicated_penalty_occurrences: int = 2
    max_related_evaluation_ids: int = 4


@dataclass(frozen=True, slots=True)
class ConsistencyConfidenceProfile:
    clean: float = 0.84
    weak_evidence_only: float = 0.72
    duplicated_penalty: float = 0.58
    missing_required_axes: float = 0.52
    unsupported_claim: float = 0.44
    cross_input_mismatch: float = 0.36


@dataclass(frozen=True, slots=True)
class ConsistencyKeywords:
    genre_keywords: Mapping[str, tuple[str, ...]]
    assertive_reason_tokens: tuple[str, ...]
    placeholder_evidence_tokens: tuple[str, ...]


CONSISTENCY_THRESHOLDS = ConsistencyThresholds()
CONSISTENCY_CONFIDENCE_PROFILE = ConsistencyConfidenceProfile()
CONSISTENCY_KEYWORDS = ConsistencyKeywords(
    genre_keywords=MappingProxyType(
        {
            "urban": ("都市", "总裁", "豪门", "职场"),
            "scifi": ("星际", "机甲", "宇宙", "赛博"),
            "fantasy": ("修仙", "宗门", "仙门", "灵气"),
            "horror": ("规则怪谈", "诡异", "惊悚"),
            "romance": ("恋爱", "婚约", "感情"),
        }
    ),
    assertive_reason_tokens=(
        "证据充分",
        "结论明确",
        "结论非常明确",
        "已经形成稳定优势",
        "具备较强",
        "显著优势",
        "完成度高",
    ),
    placeholder_evidence_tokens=("样本为空", "fallback"),
)
