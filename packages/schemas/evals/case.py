from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import InputComposition
from packages.schemas.common.validators import ensure_non_empty_text


class EvalExpectedOutcomeType(StrEnum):
    AVAILABLE = "available"
    BLOCKED = "blocked"
    FAILED = "failed"


class EvalCase(SchemaModel):
    caseId: str
    datasetRef: str
    inputComposition: InputComposition
    goal: str
    expectedOutcomeType: EvalExpectedOutcomeType
    includedInBaseline: bool

    @field_validator("caseId", "goal")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "eval case field")

    @field_validator("datasetRef")
    @classmethod
    def validate_dataset_ref(cls, value: str) -> str:
        normalized = ensure_non_empty_text(value, "datasetRef")
        if normalized.startswith(("/", "\\")) or "://" in normalized or ".." in normalized:
            raise ValueError("datasetRef 必须是仓库内相对引用。")
        return normalized


__all__ = ["EvalCase", "EvalExpectedOutcomeType"]
