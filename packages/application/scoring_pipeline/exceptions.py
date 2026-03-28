from __future__ import annotations

from dataclasses import dataclass

from packages.schemas.output.error import ErrorCode


class PipelineBlockedError(RuntimeError):
    def __init__(self, *, error_code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message

    def __str__(self) -> str:
        return self.message


class PipelineFailureError(RuntimeError):
    def __init__(self, *, error_code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message

    def __str__(self) -> str:
        return self.message
