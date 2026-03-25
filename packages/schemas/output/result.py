from __future__ import annotations

from datetime import datetime

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from typing import Literal

from packages.schemas.common.enums import AxisId, ResultStatus, SkeletonDimensionId, StageName, TopLevelScoreField
from packages.schemas.common.validators import (
    ensure_non_empty_text,
    validate_confidence,
    validate_percentage,
)


class PlatformRecommendation(SchemaModel):
    name: str
    percentage: int
    reason: str

    @field_validator("name", "reason")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "platform field")

    @field_validator("percentage")
    @classmethod
    def validate_percentage_value(cls, value: int) -> int:
        return validate_percentage(value, "percentage")


class DetailedAnalysis(SchemaModel):
    plot: str
    character: str
    pacing: str
    worldBuilding: str

    @field_validator("plot", "character", "pacing", "worldBuilding")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "detailedAnalysis field")


class FinalEvaluationProjection(SchemaModel):
    taskId: str
    stage: Literal[StageName.FINAL_PROJECTION] = StageName.FINAL_PROJECTION
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    signingProbability: int
    commercialValue: int
    writingQuality: int
    innovationScore: int
    strengths: list[str]
    weaknesses: list[str]
    platforms: list[PlatformRecommendation]
    marketFit: str
    editorVerdict: str
    detailedAnalysis: DetailedAnalysis
    overallConfidence: float
    supportingAxisMap: dict[TopLevelScoreField, list[AxisId]]
    supportingSkeletonMap: dict[TopLevelScoreField, list[SkeletonDimensionId]]

    @field_validator(
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
        "marketFit",
        "editorVerdict",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "projection field")

    @field_validator(
        "signingProbability",
        "commercialValue",
        "writingQuality",
        "innovationScore",
    )
    @classmethod
    def validate_score_fields(cls, value: int) -> int:
        return validate_percentage(value, "projection score")

    @field_validator("overallConfidence")
    @classmethod
    def validate_overall_confidence(cls, value: float) -> float:
        return validate_confidence(value, "overallConfidence")

    @field_validator("strengths", "weaknesses")
    @classmethod
    def validate_text_list(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "text list item") for item in value]

    @model_validator(mode="after")
    def validate_supporting_maps(self) -> "FinalEvaluationProjection":
        if set(self.supportingAxisMap.keys()) != set(TopLevelScoreField):
            raise ValueError("supportingAxisMap 必须覆盖全部顶层分数字段。")
        if set(self.supportingSkeletonMap.keys()) != set(TopLevelScoreField):
            raise ValueError("supportingSkeletonMap 必须覆盖全部顶层分数字段。")
        return self


class EvaluationResult(SchemaModel):
    taskId: str
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    resultTime: datetime
    signingProbability: int
    commercialValue: int
    writingQuality: int
    innovationScore: int
    strengths: list[str]
    weaknesses: list[str]
    platforms: list[PlatformRecommendation]
    marketFit: str
    editorVerdict: str
    detailedAnalysis: DetailedAnalysis

    @field_validator(
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
        "marketFit",
        "editorVerdict",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "result field")

    @field_validator(
        "signingProbability",
        "commercialValue",
        "writingQuality",
        "innovationScore",
    )
    @classmethod
    def validate_score_fields(cls, value: int) -> int:
        return validate_percentage(value, "result score")

    @field_validator("strengths", "weaknesses")
    @classmethod
    def validate_text_list(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "text list item") for item in value]


class EvaluationResultResource(SchemaModel):
    taskId: str
    resultStatus: ResultStatus
    resultTime: datetime | None = None
    result: EvaluationResult | None = None
    message: str | None = None

    @field_validator("taskId")
    @classmethod
    def validate_task_id(cls, value: str) -> str:
        return ensure_non_empty_text(value, "taskId")

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_non_empty_text(value, "message")

    @model_validator(mode="after")
    def validate_resource_state(self) -> "EvaluationResultResource":
        if self.resultStatus is ResultStatus.AVAILABLE:
            if self.result is None:
                raise ValueError("available 状态必须携带正式结果对象。")
            if self.resultTime is None:
                raise ValueError("available 状态必须携带 resultTime。")
            if self.message is not None:
                raise ValueError("available 状态不应携带结果不可用消息。")
            return self
        if self.result is not None:
            raise ValueError("blocked 或 not_available 状态不允许返回伪结果。")
        if self.resultTime is not None:
            raise ValueError("blocked 或 not_available 状态不应携带 resultTime。")
        if self.message is None:
            raise ValueError("blocked 或 not_available 状态必须携带 message。")
        return self
