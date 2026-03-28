from __future__ import annotations

from typing import Literal

from pydantic import field_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import FatalRisk, StageName
from packages.schemas.common.validators import ensure_non_empty_text, validate_confidence


class AggregatedRubricResult(SchemaModel):
    taskId: str
    stage: Literal[StageName.AGGREGATION] = StageName.AGGREGATION
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    overallVerdictDraft: str
    overallSummaryDraft: str
    platformCandidates: list[str]
    marketFitDraft: str
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

    @field_validator("platformCandidates")
    @classmethod
    def validate_platform_candidates(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "platform candidate") for item in value]

    @field_validator("overallConfidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "overallConfidence")
