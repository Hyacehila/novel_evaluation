from __future__ import annotations

from datetime import datetime

from pydantic import computed_field, field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import EvaluationMode, InputComposition, NovelType, ResultStatus, TaskStatus
from packages.schemas.common.validators import (
    ensure_non_empty_text,
    validate_confidence,
    validate_input_composition,
    validate_percentage,
)
from packages.schemas.output.error import BLOCKED_ERROR_CODES, FAILED_ERROR_CODES, ErrorCode


_ALLOWED_TASK_COMBINATIONS = {
    (TaskStatus.QUEUED, ResultStatus.NOT_AVAILABLE),
    (TaskStatus.PROCESSING, ResultStatus.NOT_AVAILABLE),
    (TaskStatus.COMPLETED, ResultStatus.AVAILABLE),
    (TaskStatus.COMPLETED, ResultStatus.BLOCKED),
    (TaskStatus.COMPLETED, ResultStatus.NOT_AVAILABLE),
    (TaskStatus.FAILED, ResultStatus.NOT_AVAILABLE),
}


class EvaluationTask(SchemaModel):
    taskId: str
    title: str
    inputSummary: str
    inputComposition: InputComposition
    hasChapters: bool
    hasOutline: bool
    evaluationMode: EvaluationMode
    status: TaskStatus
    resultStatus: ResultStatus
    errorCode: ErrorCode | None = None
    errorMessage: str | None = None
    schemaVersion: str | None = None
    promptVersion: str | None = None
    rubricVersion: str | None = None
    providerId: str | None = None
    modelId: str | None = None
    novelType: NovelType | None = None
    typeClassificationConfidence: float | None = None
    typeFallbackUsed: bool | None = None
    createdAt: datetime
    startedAt: datetime | None = None
    completedAt: datetime | None = None
    updatedAt: datetime

    @field_validator("taskId", "title", "inputSummary")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "task field")

    @field_validator("errorMessage")
    @classmethod
    def validate_optional_message(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_non_empty_text(value, "errorMessage")

    @field_validator("schemaVersion", "promptVersion", "rubricVersion", "providerId", "modelId")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_non_empty_text(value, "task metadata")

    @field_validator("typeClassificationConfidence")
    @classmethod
    def validate_type_classification_confidence(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return validate_confidence(value, "typeClassificationConfidence")

    @model_validator(mode="after")
    def validate_task_semantics(self) -> "EvaluationTask":
        validate_input_composition(
            has_chapters=self.hasChapters,
            has_outline=self.hasOutline,
            input_composition=self.inputComposition,
        )
        if (self.status, self.resultStatus) not in _ALLOWED_TASK_COMBINATIONS:
            raise ValueError("status 与 resultStatus 组合不合法。")
        if self.resultStatus is ResultStatus.BLOCKED:
            if self.errorCode is None or self.errorMessage is None:
                raise ValueError("blocked 状态必须携带错误码与错误消息。")
            if self.errorCode not in BLOCKED_ERROR_CODES:
                raise ValueError("blocked 状态必须使用阻断类错误码。")
        if self.status is TaskStatus.FAILED:
            if self.errorCode is None or self.errorMessage is None:
                raise ValueError("failed 状态必须携带错误码与错误消息。")
            if self.errorCode not in FAILED_ERROR_CODES:
                raise ValueError("failed 状态必须使用失败类错误码。")
        if self.resultStatus is ResultStatus.AVAILABLE:
            if self.errorCode is not None or self.errorMessage is not None:
                raise ValueError("available 状态不应携带错误语义。")
        if self.status in {TaskStatus.QUEUED, TaskStatus.PROCESSING}:
            if self.errorCode is not None or self.errorMessage is not None:
                raise ValueError("queued/processing 状态不应携带错误语义。")
        if self.updatedAt < self.createdAt:
            raise ValueError("updatedAt 不得早于 createdAt。")
        if self.startedAt is not None and self.startedAt < self.createdAt:
            raise ValueError("startedAt 不得早于 createdAt。")
        if self.completedAt is not None:
            reference_time = self.startedAt or self.createdAt
            if self.completedAt < reference_time:
                raise ValueError("completedAt 不得早于 startedAt 或 createdAt。")
        return self

    @computed_field
    @property
    def resultAvailable(self) -> bool:
        return self.resultStatus is ResultStatus.AVAILABLE


class EvaluationTaskSummary(SchemaModel):
    taskId: str
    title: str
    inputSummary: str
    inputComposition: InputComposition
    status: TaskStatus
    resultStatus: ResultStatus
    createdAt: datetime

    @field_validator("taskId", "title", "inputSummary")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "task summary field")

    @computed_field
    @property
    def resultAvailable(self) -> bool:
        return self.resultStatus is ResultStatus.AVAILABLE


class RecentResultSummary(SchemaModel):
    taskId: str
    title: str
    resultTime: datetime
    overallScore: int
    overallVerdict: str

    @field_validator("taskId", "title", "overallVerdict")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        return ensure_non_empty_text(value, "recent result field")

    @field_validator("overallScore")
    @classmethod
    def validate_overall_score(cls, value: int) -> int:
        return validate_percentage(value, "overallScore")
