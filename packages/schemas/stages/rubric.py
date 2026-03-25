from __future__ import annotations

from typing import Any, Literal

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import (
    AxisId,
    EvaluationMode,
    EvidenceSourceType,
    FatalRisk,
    InputComposition,
    ScoreBand,
    SkeletonDimensionId,
    StageName,
)
from packages.schemas.common.validators import (
    ensure_non_empty_text,
    validate_confidence,
)


class RubricEvaluationEvidenceRef(SchemaModel):
    sourceType: EvidenceSourceType
    sourceSpan: dict[str, Any]
    excerpt: str
    observationType: str
    evidenceNote: str
    confidence: float

    @field_validator("excerpt", "observationType", "evidenceNote")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "evidence field")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "confidence")

    @model_validator(mode="after")
    def validate_source_span(self) -> "RubricEvaluationEvidenceRef":
        if not self.sourceSpan:
            raise ValueError("sourceSpan 必须提供结构化范围。")
        return self


class RubricEvaluationItem(SchemaModel):
    evaluationId: str
    axisId: AxisId
    scoreBand: ScoreBand
    reason: str
    evidenceRefs: list[RubricEvaluationEvidenceRef]
    confidence: float
    riskTags: list[FatalRisk]
    blockingSignals: list[str]
    affectedSkeletonDimensions: list[SkeletonDimensionId]
    degradedByInput: bool

    @field_validator("evaluationId", "reason")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "rubric item field")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "confidence")

    @field_validator("blockingSignals")
    @classmethod
    def validate_blocking_signals(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "blockingSignal") for item in value]

    @model_validator(mode="after")
    def validate_item(self) -> "RubricEvaluationItem":
        if not self.evidenceRefs:
            raise ValueError("RubricEvaluationItem 至少需要一条证据引用。")
        return self


class RubricEvaluationSet(SchemaModel):
    taskId: str
    stage: Literal[StageName.RUBRIC_EVALUATION] = StageName.RUBRIC_EVALUATION
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    inputComposition: InputComposition
    evaluationMode: EvaluationMode
    items: list[RubricEvaluationItem]
    axisSummaries: dict[AxisId, str]
    missingRequiredAxes: list[AxisId]
    riskTags: list[FatalRisk]
    overallConfidence: float

    @field_validator(
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "rubric set field")

    @field_validator("axisSummaries")
    @classmethod
    def validate_axis_summaries(cls, value: dict[AxisId, str]) -> dict[AxisId, str]:
        return {
            axis_id: ensure_non_empty_text(summary, "axis summary value")
            for axis_id, summary in value.items()
        }

    @field_validator("overallConfidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "overallConfidence")

    @model_validator(mode="after")
    def validate_axis_coverage(self) -> "RubricEvaluationSet":
        observed_axes = {item.axisId for item in self.items}
        required_axes = set(AxisId)
        missing_axes = required_axes - observed_axes
        if missing_axes:
            raise ValueError("RubricEvaluationSet 必须覆盖全部 8 轴。")
        if set(self.axisSummaries.keys()) != required_axes:
            raise ValueError("axisSummaries 必须覆盖全部 8 轴。")
        if self.evaluationMode is EvaluationMode.FULL and self.missingRequiredAxes:
            raise ValueError("full 模式下 missingRequiredAxes 必须为空。")
        return self
