from __future__ import annotations

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import InputComposition, ResultStatus, TaskStatus
from packages.schemas.common.validators import ensure_non_empty_text, ensure_optional_text
from packages.schemas.evals import EvalExpectedOutcomeType
from packages.schemas.output.error import ErrorCode


class EvalDatasetEntry(SchemaModel):
    caseId: str
    title: str
    inputComposition: InputComposition
    chaptersRef: str | None = None
    chaptersContent: str | None = None
    outlineRef: str | None = None
    outlineContent: str | None = None
    expectedOutcomeType: EvalExpectedOutcomeType
    includedInBaseline: bool
    notes: str | None = None

    @field_validator("caseId", "title")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "eval dataset field")

    @field_validator("chaptersRef", "chaptersContent", "outlineRef", "outlineContent", "notes")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        return ensure_optional_text(value, "eval dataset optional field")

    @model_validator(mode="after")
    def validate_input_sources(self) -> "EvalDatasetEntry":
        has_chapters = self.chaptersRef is not None or self.chaptersContent is not None
        has_outline = self.outlineRef is not None or self.outlineContent is not None
        if self.inputComposition is InputComposition.CHAPTERS_OUTLINE and (not has_chapters or not has_outline):
            raise ValueError("chapters_outline 样本必须同时提供 chapters 与 outline。")
        if self.inputComposition is InputComposition.CHAPTERS_ONLY and (not has_chapters or has_outline):
            raise ValueError("chapters_only 样本必须只提供 chapters。")
        if self.inputComposition is InputComposition.OUTLINE_ONLY and (not has_outline or has_chapters):
            raise ValueError("outline_only 样本必须只提供 outline。")
        return self


class PromptMetadataSnapshot(SchemaModel):
    promptId: str
    promptVersion: str
    stage: str
    schemaVersion: str
    rubricVersion: str
    registryStatus: str
    versionStatus: str
    enabled: bool

    @field_validator(
        "promptId",
        "promptVersion",
        "stage",
        "schemaVersion",
        "rubricVersion",
        "registryStatus",
        "versionStatus",
    )
    @classmethod
    def validate_required_snapshot_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "prompt metadata field")


class RecordBuildInput(SchemaModel):
    evalCaseId: str
    taskId: str
    taskStatus: TaskStatus
    resultStatus: ResultStatus
    errorCode: ErrorCode | None = None
    errorMessage: str | None = None
    durationMs: int
    schemaValid: bool

    @field_validator("evalCaseId", "taskId")
    @classmethod
    def validate_required_record_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "record build field")

    @field_validator("errorMessage")
    @classmethod
    def validate_optional_record_text(cls, value: str | None) -> str | None:
        return ensure_optional_text(value, "record build errorMessage")

    @field_validator("durationMs")
    @classmethod
    def validate_duration_ms(cls, value: int) -> int:
        if value < 0:
            raise ValueError("durationMs 不能为负数。")
        return value


__all__ = [
    "EvalDatasetEntry",
    "PromptMetadataSnapshot",
    "RecordBuildInput",
]
