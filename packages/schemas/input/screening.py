from __future__ import annotations

from typing import Any, Literal

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import (
    EvaluationMode,
    FatalRisk,
    InputComposition,
    StageName,
    StageStatus,
    Sufficiency,
)
from packages.schemas.common.validators import (
    ensure_non_empty_text,
    validate_confidence,
    validate_input_composition,
)


class InputScreeningResult(SchemaModel):
    taskId: str
    stage: Literal[StageName.INPUT_SCREENING] = StageName.INPUT_SCREENING
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    inputComposition: InputComposition
    hasChapters: bool
    hasOutline: bool
    chaptersSufficiency: Sufficiency
    outlineSufficiency: Sufficiency
    evaluationMode: EvaluationMode
    rateable: bool
    status: StageStatus
    rejectionReasons: list[str]
    riskTags: list[FatalRisk]
    segmentationPlan: dict[str, Any] | None = None
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
        return ensure_non_empty_text(value, "stage field")

    @field_validator("rejectionReasons")
    @classmethod
    def validate_rejection_reasons(cls, value: list[str]) -> list[str]:
        return [ensure_non_empty_text(item, "rejectionReason") for item in value]

    @field_validator("confidence")
    @classmethod
    def validate_confidence_value(cls, value: float) -> float:
        return validate_confidence(value, "confidence")

    @model_validator(mode="after")
    def validate_stage_semantics(self) -> "InputScreeningResult":
        validate_input_composition(
            has_chapters=self.hasChapters,
            has_outline=self.hasOutline,
            input_composition=self.inputComposition,
        )
        if self.evaluationMode is EvaluationMode.FULL:
            if self.inputComposition is not InputComposition.CHAPTERS_OUTLINE:
                raise ValueError("full 模式要求同时存在正文与大纲。")
            if self.chaptersSufficiency is not Sufficiency.SUFFICIENT:
                raise ValueError("full 模式要求 chaptersSufficiency 为 sufficient。")
            if self.outlineSufficiency is not Sufficiency.SUFFICIENT:
                raise ValueError("full 模式要求 outlineSufficiency 为 sufficient。")
        if not self.rateable:
            if not self.rejectionReasons:
                raise ValueError("不可评输入必须提供 rejectionReasons。")
            if self.continueAllowed:
                raise ValueError("不可评输入不允许继续进入下游阶段。")
        if self.status is StageStatus.FAILED and self.continueAllowed:
            raise ValueError("阶段失败时不允许 continueAllowed=true。")
        return self
