from __future__ import annotations

from typing import Protocol

from .contracts import ProviderExecutionRequest, ProviderExecutionResult


class ProviderAdapter(Protocol):
    provider_id: str
    model_id: str

    def execute(self, request: ProviderExecutionRequest) -> ProviderExecutionResult:
        ...
