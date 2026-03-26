from __future__ import annotations

from datetime import datetime

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.validators import ensure_non_empty_text


class EvalExecutionSummary(SchemaModel):
    totalCount: int
    availableCount: int
    blockedCount: int
    failedCount: int
    schemaValidCount: int

    @field_validator("totalCount", "availableCount", "blockedCount", "failedCount", "schemaValidCount")
    @classmethod
    def validate_non_negative_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("summary count 不能为负数。")
        return value

    @model_validator(mode="after")
    def validate_count_consistency(self) -> "EvalExecutionSummary":
        if self.availableCount + self.blockedCount + self.failedCount != self.totalCount:
            raise ValueError("summary 中的 outcome 数量之和必须等于 totalCount。")
        if self.schemaValidCount > self.totalCount:
            raise ValueError("schemaValidCount 不能大于 totalCount。")
        if self.schemaValidCount > self.availableCount:
            raise ValueError("schemaValidCount 不能大于 availableCount。")
        return self


class EvalBaseline(SchemaModel):
    baselineId: str
    caseIds: tuple[str, ...]
    promptVersion: str
    schemaVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    createdAt: datetime
    summary: EvalExecutionSummary

    @field_validator("baselineId", "promptVersion", "schemaVersion", "rubricVersion", "providerId", "modelId")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "eval baseline field")

    @field_validator("caseIds")
    @classmethod
    def validate_case_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("caseIds 不能为空。")
        normalized = tuple(ensure_non_empty_text(case_id, "caseId") for case_id in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("caseIds 不允许重复。")
        return normalized

    @model_validator(mode="after")
    def validate_summary_alignment(self) -> "EvalBaseline":
        if self.summary.totalCount != len(self.caseIds):
            raise ValueError("summary.totalCount 必须与 caseIds 数量一致。")
        return self


__all__ = ["EvalBaseline", "EvalExecutionSummary"]
