from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import AxisId, FatalRisk, ResultStatus, ScoreBand, StageName
from packages.schemas.common.validators import (
    ensure_non_empty_text,
    ensure_optional_text,
    validate_percentage,
)
from packages.schemas.stages.aggregation import PlatformCandidate


class AxisEvaluationResult(SchemaModel):
    axisId: AxisId
    scoreBand: ScoreBand
    score: int
    summary: str
    reason: str
    degradedByInput: bool
    riskTags: list[FatalRisk]

    @field_validator("summary", "reason")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "axis result field")

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: int) -> int:
        return validate_percentage(value, "axis score")


class OverallEvaluationResult(SchemaModel):
    score: int
    verdict: str
    verdictSubQuote: str | None = None   # 市场分析副句，与主判断形成双层结构
    summary: str
    platformCandidates: list[PlatformCandidate]
    marketFit: str
    strengths: list[str] = []
    weaknesses: list[str] = []

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: int) -> int:
        return validate_percentage(value, "overall score")

    @field_validator("verdict", "summary", "marketFit")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "overall field")

    @field_validator("verdictSubQuote")
    @classmethod
    def validate_optional_text_field(cls, value: str | None) -> str | None:
        return ensure_optional_text(value, "overall optional field")

    @field_validator("strengths", "weaknesses")
    @classmethod
    def validate_text_list_fields(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "overall list item") for item in value]

    @model_validator(mode="after")
    def validate_platform_candidate_weights(self) -> "OverallEvaluationResult":
        if self.platformCandidates and sum(candidate.weight for candidate in self.platformCandidates) != 100:
            raise ValueError("platformCandidates 权重之和必须为 100。")
        return self


class FinalEvaluationProjection(SchemaModel):
    taskId: str
    stage: Literal[StageName.FINAL_PROJECTION] = StageName.FINAL_PROJECTION
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    axes: list[AxisEvaluationResult]
    overall: OverallEvaluationResult

    @field_validator(
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "projection field")

    @model_validator(mode="after")
    def validate_axes_coverage(self) -> "FinalEvaluationProjection":
        if len(self.axes) != len(AxisId):
            raise ValueError("axes 必须覆盖全部 8 个 rubric 轴。")
        axis_ids = [axis.axisId for axis in self.axes]
        if len(set(axis_ids)) != len(AxisId) or set(axis_ids) != set(AxisId):
            raise ValueError("axes 必须完整且唯一覆盖全部 AxisId。")
        return self


class EvaluationResult(SchemaModel):
    taskId: str
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    resultTime: datetime
    axes: list[AxisEvaluationResult]
    overall: OverallEvaluationResult

    @field_validator(
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "result field")

    @model_validator(mode="after")
    def validate_axes_coverage(self) -> "EvaluationResult":
        if len(self.axes) != len(AxisId):
            raise ValueError("axes 必须覆盖全部 8 个 rubric 轴。")
        axis_ids = [axis.axisId for axis in self.axes]
        if len(set(axis_ids)) != len(AxisId) or set(axis_ids) != set(AxisId):
            raise ValueError("axes 必须完整且唯一覆盖全部 AxisId。")
        return self


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
