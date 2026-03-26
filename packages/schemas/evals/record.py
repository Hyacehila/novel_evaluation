from __future__ import annotations

from pydantic import field_validator, model_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.enums import ResultStatus, TaskStatus
from packages.schemas.common.validators import ensure_non_empty_text
from packages.schemas.output.error import BLOCKED_ERROR_CODES, FAILED_ERROR_CODES, ErrorCode


_ALLOWED_EVAL_RECORD_COMBINATIONS = {
    (TaskStatus.COMPLETED, ResultStatus.AVAILABLE),
    (TaskStatus.COMPLETED, ResultStatus.BLOCKED),
    (TaskStatus.FAILED, ResultStatus.NOT_AVAILABLE),
}


class EvalRecord(SchemaModel):
    evalCaseId: str
    taskId: str
    schemaVersion: str
    promptVersion: str
    rubricVersion: str
    providerId: str
    modelId: str
    taskStatus: TaskStatus
    resultStatus: ResultStatus
    errorCode: ErrorCode | None = None
    errorMessage: str | None = None
    durationMs: int
    schemaValid: bool

    @field_validator(
        "evalCaseId",
        "taskId",
        "schemaVersion",
        "promptVersion",
        "rubricVersion",
        "providerId",
        "modelId",
    )
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        return ensure_non_empty_text(value, "eval record field")

    @field_validator("errorMessage")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return ensure_non_empty_text(value, "eval record errorMessage")

    @field_validator("durationMs")
    @classmethod
    def validate_duration_ms(cls, value: int) -> int:
        if value < 0:
            raise ValueError("durationMs 不能为负数。")
        return value

    @model_validator(mode="after")
    def validate_record_state(self) -> "EvalRecord":
        if (self.taskStatus, self.resultStatus) not in _ALLOWED_EVAL_RECORD_COMBINATIONS:
            raise ValueError("EvalRecord 只允许终态状态组合。")

        if self.resultStatus is ResultStatus.AVAILABLE:
            if self.errorCode is not None or self.errorMessage is not None:
                raise ValueError("available 记录不应携带错误语义。")
            if not self.schemaValid:
                raise ValueError("available 记录必须声明 schemaValid=true。")
            return self

        if self.errorCode is None or self.errorMessage is None:
            raise ValueError("blocked 或 failed 记录必须携带错误码与错误消息。")
        if self.schemaValid:
            raise ValueError("blocked 或 failed 记录不应声明 schemaValid=true。")

        if self.taskStatus is TaskStatus.COMPLETED:
            if self.errorCode not in BLOCKED_ERROR_CODES:
                raise ValueError("blocked 记录必须使用阻断类错误码。")
            return self

        if self.errorCode not in FAILED_ERROR_CODES:
            raise ValueError("failed 记录必须使用失败类错误码。")
        return self


__all__ = ["EvalRecord"]
