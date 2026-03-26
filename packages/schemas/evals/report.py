from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.validators import ensure_non_empty_text
from packages.schemas.evals.baseline import EvalExecutionSummary


class EvalReportType(StrEnum):
    EXECUTION_SUMMARY = "execution_summary"
    BASELINE_COMPARISON = "baseline_comparison"


class EvalBaselineComparison(SchemaModel):
    baselineId: str
    changedCaseIds: tuple[str, ...]
    availableDelta: int
    blockedDelta: int
    failedDelta: int
    schemaValidDelta: int

    @field_validator("baselineId")
    @classmethod
    def validate_baseline_id(cls, value: str) -> str:
        return ensure_non_empty_text(value, "baselineId")

    @field_validator("changedCaseIds")
    @classmethod
    def validate_changed_case_ids(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(ensure_non_empty_text(case_id, "changedCaseId") for case_id in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("changedCaseIds 不允许重复。")
        return normalized


class EvalReport(SchemaModel):
    reportId: str
    reportType: EvalReportType
    caseIds: tuple[str, ...]
    promptVersion: str
    schemaVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    createdAt: datetime
    summary: EvalExecutionSummary
    comparison: EvalBaselineComparison | None = None

    @field_validator("reportId", "promptVersion", "schemaVersion", "rubricVersion", "providerId", "modelId")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "eval report field")

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
    def validate_report_semantics(self) -> "EvalReport":
        if self.summary.totalCount != len(self.caseIds):
            raise ValueError("summary.totalCount 必须与 caseIds 数量一致。")
        if self.reportType is EvalReportType.BASELINE_COMPARISON:
            if self.comparison is None:
                raise ValueError("baseline_comparison 报告必须携带 comparison。")
            case_id_set = set(self.caseIds)
            changed_case_id_set = set(self.comparison.changedCaseIds)
            if not changed_case_id_set.issubset(case_id_set):
                raise ValueError("comparison.changedCaseIds 必须是 caseIds 的子集。")
            if not changed_case_id_set and any(
                delta != 0
                for delta in (
                    self.comparison.availableDelta,
                    self.comparison.blockedDelta,
                    self.comparison.failedDelta,
                    self.comparison.schemaValidDelta,
                )
            ):
                raise ValueError("存在 delta 变化时必须提供 changedCaseIds。")
            return self
        if self.comparison is not None:
            raise ValueError("execution_summary 报告不应携带 comparison。")
        return self


__all__ = ["EvalBaselineComparison", "EvalReport", "EvalReportType"]
