from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.schemas.common.enums import EvaluationMode, InputComposition, StageName
from packages.schemas.output.error import ErrorCode

PROVIDER_ADAPTERS_SRC = Path(__file__).resolve().parents[3] / "packages" / "provider-adapters" / "src"

provider_adapters_src = str(PROVIDER_ADAPTERS_SRC)
if provider_adapters_src not in sys.path:
    sys.path.insert(0, provider_adapters_src)

from provider_adapters import (  # noqa: E402
    LocalAdapterMode,
    LocalDeterministicProviderAdapter,
    ProviderExecutionFailure,
    ProviderExecutionRequest,
    ProviderExecutionSuccess,
    ProviderFailureType,
    ProviderMessage,
    build_provider_failure,
    map_failure_type_to_error_code,
)


def build_request(
    *,
    messages: list[ProviderMessage] | None = None,
    provider_id: str = "provider-local",
    model_id: str = "model-local",
) -> ProviderExecutionRequest:
    return ProviderExecutionRequest(
        taskId="task_20260326_001",
        stage=StageName.RUBRIC_EVALUATION,
        promptId="rubric-prompt",
        promptVersion="2026-03-26",
        schemaVersion="1.0.0",
        rubricVersion="rubric-v1",
        providerId=provider_id,
        modelId=model_id,
        requestId="req_20260326_001",
        messages=messages if messages is not None else [ProviderMessage(role="user", content="请输出结构化分析")],
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        evaluationMode=EvaluationMode.FULL,
        timeoutMs=3000,
        responseFormat={"type": "json_object"},
    )


def test_provider_request_matches_phase_one_contract() -> None:
    request = build_request()

    payload = request.model_dump(mode="json")

    assert payload["stage"] == "rubric_evaluation"
    assert payload["inputComposition"] == "chapters_outline"
    assert payload["evaluationMode"] == "full"
    assert payload["messages"][0] == {"role": "user", "content": "请输出结构化分析"}


def test_local_adapter_returns_typed_success() -> None:
    adapter = LocalDeterministicProviderAdapter()

    result = adapter.execute(build_request())

    assert isinstance(result, ProviderExecutionSuccess)
    assert result.providerId == "provider-local"
    assert result.modelId == "model-local"
    assert result.requestId == "req_20260326_001"
    assert result.providerRequestId == "local-req_20260326_001"
    assert result.durationMs == 5
    assert dict(result.rawJson) == {
        "adapter": "local_deterministic",
        "taskId": "task_20260326_001",
        "stage": "rubric_evaluation",
        "messageCount": 1,
        "messages": ({"role": "user", "content": "请输出结构化分析"},),
    }
    assert result.rawText == json.dumps(
        {
            "adapter": "local_deterministic",
            "taskId": "task_20260326_001",
            "stage": "rubric_evaluation",
            "messageCount": 1,
            "messages": [{"role": "user", "content": "请输出结构化分析"}],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    assert result.__class__.model_config["frozen"] is True
    assert "providerRequestId" in result.model_dump()


@pytest.mark.parametrize(
    ("mode", "failure_type", "error_code", "retryable", "provider_request_id"),
    [
        (
            LocalAdapterMode.PROVIDER_FAILURE,
            ProviderFailureType.PROVIDER_FAILURE,
            ErrorCode.PROVIDER_FAILURE,
            True,
            "local-req_20260326_001",
        ),
        (
            LocalAdapterMode.TIMEOUT,
            ProviderFailureType.TIMEOUT,
            ErrorCode.TIMEOUT,
            True,
            "local-req_20260326_001",
        ),
        (
            LocalAdapterMode.DEPENDENCY_UNAVAILABLE,
            ProviderFailureType.DEPENDENCY_UNAVAILABLE,
            ErrorCode.DEPENDENCY_UNAVAILABLE,
            True,
            None,
        ),
        (
            LocalAdapterMode.CONTRACT_INVALID,
            ProviderFailureType.CONTRACT_INVALID,
            ErrorCode.CONTRACT_INVALID,
            False,
            None,
        ),
    ],
)
def test_local_adapter_maps_failure_modes(
    mode: LocalAdapterMode,
    failure_type: ProviderFailureType,
    error_code: ErrorCode,
    retryable: bool,
    provider_request_id: str | None,
) -> None:
    adapter = LocalDeterministicProviderAdapter(mode=mode)

    result = adapter.execute(build_request())

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is failure_type
    assert map_failure_type_to_error_code(result.failureType) is error_code
    assert result.retryable is retryable
    assert result.providerRequestId == provider_request_id
    assert result.durationMs == 5
    assert result.__class__.model_config["frozen"] is True
    assert "providerRequestId" in result.model_dump()


def test_local_adapter_allows_provider_failure_retryable_override() -> None:
    adapter = LocalDeterministicProviderAdapter(
        mode=LocalAdapterMode.PROVIDER_FAILURE,
        provider_failure_retryable=False,
    )

    result = adapter.execute(build_request())

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.PROVIDER_FAILURE
    assert result.retryable is False


def test_provider_request_rejects_empty_messages() -> None:
    with pytest.raises(ValidationError):
        build_request(messages=[])


def test_local_adapter_returns_deeply_frozen_raw_json() -> None:
    adapter = LocalDeterministicProviderAdapter()

    result = adapter.execute(build_request())

    assert isinstance(result, ProviderExecutionSuccess)
    with pytest.raises(TypeError):
        result.rawJson["adapter"] = "mutated"
    with pytest.raises(TypeError):
        result.rawJson["messages"][0]["role"] = "assistant"


def test_local_adapter_rejects_mismatched_provider_identity() -> None:
    adapter = LocalDeterministicProviderAdapter(provider_id="provider-local", model_id="model-local")

    result = adapter.execute(build_request(provider_id="provider-other", model_id="model-other"))

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.CONTRACT_INVALID
    assert result.providerId == "provider-local"
    assert result.modelId == "model-local"
    assert result.retryable is False
    assert result.providerRequestId is None


def test_build_provider_failure_uses_default_retryable_mapping() -> None:
    failure = build_provider_failure(
        provider_id="provider-local",
        model_id="model-local",
        request_id="req_20260326_001",
        provider_request_id=None,
        duration_ms=8,
        failure_type=ProviderFailureType.TIMEOUT,
        message="timeout",
    )

    assert failure.failureType is ProviderFailureType.TIMEOUT
    assert failure.retryable is True


def test_local_adapter_never_accesses_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_connect(self: socket.socket, address: object) -> None:
        raise AssertionError(f"unexpected network access: {address}")

    monkeypatch.setattr(socket.socket, "connect", fail_connect)
    adapter = LocalDeterministicProviderAdapter()

    result = adapter.execute(build_request())

    assert isinstance(result, ProviderExecutionSuccess)
