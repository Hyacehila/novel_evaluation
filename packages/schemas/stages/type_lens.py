from __future__ import annotations

from typing import Literal

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import EvaluationMode, FatalRisk, InputComposition, NovelType, ScoreBand, StageName
from packages.schemas.common.novel_types import get_type_lens_ids
from packages.schemas.common.validators import ensure_non_empty_text, validate_confidence
from packages.schemas.stages.rubric import RubricEvaluationEvidenceRef


class TypeLensItem(SchemaModel):
    lensId: str
    label: str
    scoreBand: ScoreBand
    reason: str
    evidenceRefs: list[RubricEvaluationEvidenceRef]
    confidence: float
    riskTags: list[FatalRisk]
    degradedByInput: bool

    @field_validator("lensId", "label", "reason")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "type lens field")

    @field_validator("confidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "type lens confidence")

    @model_validator(mode="after")
    def validate_evidence_refs(self) -> "TypeLensItem":
        if not self.evidenceRefs:
            raise ValueError("TypeLensItem 至少需要一条证据引用。")
        return self


class TypeLensEvaluationResult(SchemaModel):
    taskId: str
    stage: Literal[StageName.TYPE_LENS_EVALUATION] = StageName.TYPE_LENS_EVALUATION
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    inputComposition: InputComposition
    evaluationMode: EvaluationMode
    novelType: NovelType
    summary: str
    items: list[TypeLensItem]
    overallConfidence: float

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
        return ensure_non_empty_text(value, "type lens field")

    @field_validator("overallConfidence")
    @classmethod
    def validate_overall_confidence(cls, value: float) -> float:
        return validate_confidence(value, "overallConfidence")

    @model_validator(mode="after")
    def validate_item_coverage(self) -> "TypeLensEvaluationResult":
        expected_lens_ids = set(get_type_lens_ids(self.novelType))
        observed_lens_ids = [item.lensId for item in self.items]
        if len(observed_lens_ids) != len(expected_lens_ids):
            raise ValueError("type lens 结果必须完整覆盖 4 个 lens。")
        if len(set(observed_lens_ids)) != len(observed_lens_ids):
            raise ValueError("type lens 结果不允许重复 lensId。")
        if set(observed_lens_ids) != expected_lens_ids:
            raise ValueError("type lens 结果必须与当前 novelType 的固定 lens 集合完全一致。")
        return self
