from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import AxisId, EvaluationMode, InputComposition, StageName
from packages.schemas.common.validators import ensure_non_empty_text, validate_confidence


class ConflictType(StrEnum):
    CROSS_INPUT_MISMATCH = "cross_input_mismatch"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    DUPLICATED_PENALTY = "duplicated_penalty"
    MISSING_REQUIRED_AXIS = "missing_required_axis"
    WEAK_EVIDENCE = "weak_evidence"


class ConflictSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConsistencyConflict(SchemaModel):
    conflictId: str
    conflictType: ConflictType
    relatedEvaluationIds: list[str]
    description: str
    severity: ConflictSeverity
    normalizationNote: str

    @field_validator("conflictId", "description", "normalizationNote")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "conflict field")

    @field_validator("relatedEvaluationIds")
    @classmethod
    def validate_related_ids(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "relatedEvaluationId") for item in value]


class ConsistencyCheckResult(SchemaModel):
    taskId: str
    stage: Literal[StageName.CONSISTENCY_CHECK] = StageName.CONSISTENCY_CHECK
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    inputComposition: InputComposition
    evaluationMode: EvaluationMode
    passed: bool
    conflicts: list[ConsistencyConflict]
    crossInputMismatchDetected: bool
    unsupportedClaimsDetected: bool
    duplicatedPenaltiesDetected: bool
    missingRequiredAxes: list[AxisId]
    normalizationNotes: list[str]
    confidence: float
    continueAllowed: bool

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
        return ensure_non_empty_text(value, "consistency field")

    @field_validator("normalizationNotes")
    @classmethod
    def validate_notes(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "normalizationNote") for item in value]

    @field_validator("confidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "confidence")

    @model_validator(mode="after")
    def validate_continue_allowed(self) -> "ConsistencyCheckResult":
        if self.continueAllowed and not self.passed:
            raise ValueError("未通过一致性整理时不允许 continueAllowed=true。")
        return self
