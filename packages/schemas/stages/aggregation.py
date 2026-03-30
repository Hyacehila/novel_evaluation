from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import FatalRisk, StageName
from packages.schemas.common.validators import ensure_non_empty_text, ensure_optional_text, validate_confidence, validate_percentage


class PlatformCandidate(SchemaModel):
    """平台推荐候选，包含权重与针对该平台圈层的推介语。"""

    name: str
    weight: int       # 推荐权重，0-100，多个平台权重之和应为 100
    pitchQuote: str   # 针对该平台核心读者圈层的一句推介语

    @field_validator("name", "pitchQuote")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "PlatformCandidate field")

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value: int) -> int:
        return validate_percentage(value, "PlatformCandidate.weight")


class AggregatedRubricResult(SchemaModel):
    taskId: str
    stage: Literal[StageName.AGGREGATION] = StageName.AGGREGATION
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    overallVerdictDraft: str
    verdictSubQuote: str | None = None   # 市场分析副句，与主判断形成双层结构
    overallSummaryDraft: str
    platformCandidates: list[PlatformCandidate]
    marketFitDraft: str
    strengthCandidates: list[str] = []
    weaknessCandidates: list[str] = []
    riskTags: list[FatalRisk]
    overallConfidence: float

    @field_validator(
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
        "overallVerdictDraft",
        "overallSummaryDraft",
        "marketFitDraft",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "aggregation field")

    @field_validator("verdictSubQuote")
    @classmethod
    def validate_optional_text_field(cls, value: str | None) -> str | None:
        return ensure_optional_text(value, "aggregation optional field")

    @field_validator("strengthCandidates", "weaknessCandidates")
    @classmethod
    def validate_text_list_fields(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "aggregation list item") for item in value]

    @field_validator("overallConfidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "overallConfidence")

    @model_validator(mode="after")
    def validate_platform_candidate_weights(self) -> "AggregatedRubricResult":
        if self.platformCandidates and sum(candidate.weight for candidate in self.platformCandidates) != 100:
            raise ValueError("platformCandidates 权重之和必须为 100。")
        return self
