from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import EvaluationMode, InputComposition, NovelType, StageName
from packages.schemas.common.validators import ensure_non_empty_text, validate_confidence


class TypeClassificationCandidate(SchemaModel):
    novelType: NovelType
    confidence: float
    reason: str

    @field_validator("confidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "candidate confidence")

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        return ensure_non_empty_text(value, "candidate reason")


class TypeClassificationResult(SchemaModel):
    taskId: str
    stage: Literal[StageName.TYPE_CLASSIFICATION] = StageName.TYPE_CLASSIFICATION
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    inputComposition: InputComposition
    evaluationMode: EvaluationMode
    candidates: list[TypeClassificationCandidate]
    novelType: NovelType
    classificationConfidence: float
    fallbackUsed: bool
    summary: str

    @field_validator(
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
        "summary",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "type classification field")

    @field_validator("classificationConfidence")
    @classmethod
    def validate_classification_confidence(cls, value: float) -> float:
        return validate_confidence(value, "classificationConfidence")

    @model_validator(mode="after")
    def validate_candidates(self) -> "TypeClassificationResult":
        if len(self.candidates) != 3:
            raise ValueError("type classification 必须输出 Top-3 候选。")
        candidate_types = [candidate.novelType for candidate in self.candidates]
        if len(set(candidate_types)) != len(candidate_types):
            raise ValueError("type classification 候选类型不允许重复。")
        if not self.fallbackUsed and self.novelType not in candidate_types:
            raise ValueError("非 fallback 场景下 novelType 必须来自候选集合。")
        return self
