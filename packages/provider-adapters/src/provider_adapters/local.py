from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum

from .contracts import (
    ProviderExecutionFailure,
    ProviderExecutionRequest,
    ProviderExecutionResult,
    ProviderExecutionSuccess,
    ProviderFailureType,
    build_provider_failure,
)


class LocalAdapterMode(StrEnum):
    SUCCESS = "success"
    PROVIDER_FAILURE = ProviderFailureType.PROVIDER_FAILURE.value
    TIMEOUT = ProviderFailureType.TIMEOUT.value
    DEPENDENCY_UNAVAILABLE = ProviderFailureType.DEPENDENCY_UNAVAILABLE.value
    CONTRACT_INVALID = ProviderFailureType.CONTRACT_INVALID.value


@dataclass(frozen=True, slots=True)
class LocalDeterministicProviderAdapter:
    provider_id: str = "provider-local"
    model_id: str = "model-local"
    mode: LocalAdapterMode = LocalAdapterMode.SUCCESS
    duration_ms: int = 5
    provider_failure_retryable: bool | None = None

    def execute(self, request: ProviderExecutionRequest) -> ProviderExecutionResult:
        if request.providerId != self.provider_id or request.modelId != self.model_id:
            return build_provider_failure(
                provider_id=self.provider_id,
                model_id=self.model_id,
                request_id=request.requestId,
                provider_request_id=None,
                duration_ms=self.duration_ms,
                failure_type=ProviderFailureType.CONTRACT_INVALID,
                message="本地 deterministic adapter 收到与自身不匹配的 providerId 或 modelId。",
            )
        if self.mode is LocalAdapterMode.SUCCESS:
            return self._build_success(request)

        failure_type = ProviderFailureType(self.mode.value)
        provider_request_id = self._build_provider_request_id(request)
        if failure_type in {
            ProviderFailureType.DEPENDENCY_UNAVAILABLE,
            ProviderFailureType.CONTRACT_INVALID,
        }:
            provider_request_id = None

        return self._build_failure(
            request=request,
            failure_type=failure_type,
            provider_request_id=provider_request_id,
            message=self._build_failure_message(failure_type),
        )

    def _build_success(self, request: ProviderExecutionRequest) -> ProviderExecutionSuccess:
        provider_request_id = self._build_provider_request_id(request)
        raw_json = {
            "adapter": "local_deterministic",
            "taskId": request.taskId,
            "stage": request.stage.value,
            "messageCount": len(request.messages),
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
        }
        raw_text = json.dumps(raw_json, ensure_ascii=False, sort_keys=True)
        return ProviderExecutionSuccess(
            providerId=self.provider_id,
            modelId=self.model_id,
            requestId=request.requestId,
            providerRequestId=provider_request_id,
            durationMs=self.duration_ms,
            rawText=raw_text,
            rawJson=raw_json,
        )

    def _build_failure(
        self,
        *,
        request: ProviderExecutionRequest,
        failure_type: ProviderFailureType,
        provider_request_id: str | None,
        message: str,
    ) -> ProviderExecutionFailure:
        retryable = self.provider_failure_retryable if failure_type is ProviderFailureType.PROVIDER_FAILURE else None
        return build_provider_failure(
            provider_id=self.provider_id,
            model_id=self.model_id,
            request_id=request.requestId,
            provider_request_id=provider_request_id,
            duration_ms=self.duration_ms,
            failure_type=failure_type,
            message=message,
            retryable=retryable,
        )

    def _build_provider_request_id(self, request: ProviderExecutionRequest) -> str:
        return f"local-{request.requestId}"

    def _build_failure_message(self, failure_type: ProviderFailureType) -> str:
        if failure_type is ProviderFailureType.PROVIDER_FAILURE:
            return "本地 deterministic adapter 模拟 provider_failure。"
        if failure_type is ProviderFailureType.TIMEOUT:
            return "本地 deterministic adapter 模拟 timeout。"
        if failure_type is ProviderFailureType.DEPENDENCY_UNAVAILABLE:
            return "本地 deterministic adapter 模拟 dependency_unavailable。"
        return "本地 deterministic adapter 模拟 contract_invalid。"
