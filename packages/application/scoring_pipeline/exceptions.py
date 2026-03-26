from __future__ import annotations

from dataclasses import dataclass

from packages.schemas.output.error import ErrorCode


@dataclass(frozen=True, slots=True)
class PipelineBlockedError(RuntimeError):
    error_code: ErrorCode
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class PipelineFailureError(RuntimeError):
    error_code: ErrorCode
    message: str

    def __str__(self) -> str:
        return self.message
