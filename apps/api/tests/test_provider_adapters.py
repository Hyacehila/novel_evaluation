from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from packages.schemas.common.enums import EvaluationMode, InputComposition, StageName
from packages.schemas.output.error import ErrorCode

PROVIDER_ADAPTERS_SRC = Path(__file__).resolve().parents[3] / "packages" / "provider-adapters" / "src"

provider_adapters_src = str(PROVIDER_ADAPTERS_SRC)
if provider_adapters_src not in sys.path:
    sys.path.insert(0, provider_adapters_src)

from provider_adapters import (  # noqa: E402
    DeepSeekProviderAdapter,
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

_USE_DEFAULT_RESPONSE_FORMAT = object()


def build_request(
    *,
    messages: list[ProviderMessage] | None = None,
    provider_id: str = "provider-local",
    model_id: str = "model-local",
    timeout_ms: int | None = 3000,
    max_tokens: int | None = None,
    response_format: str | dict[str, object] | None | object = _USE_DEFAULT_RESPONSE_FORMAT,
) -> ProviderExecutionRequest:
    resolved_response_format = {"type": "json_object"} if response_format is _USE_DEFAULT_RESPONSE_FORMAT else response_format
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
        timeoutMs=timeout_ms,
        maxTokens=max_tokens,
        responseFormat=resolved_response_format,
    )


class FakeDeepSeekResponse:
    def __init__(
        self,
        *,
        content: str = '{"score": 95}',
        request_id: str = "deepseek-request-001",
        parsed: object | None = None,
        finish_reason: str | None = None,
    ) -> None:
        self.id = request_id
        self.choices = [
            type(
                "FakeChoice",
                (),
                {
                    "message": type(
                        "FakeMessage",
                        (),
                        {
                            "content": content,
                            "parsed": parsed,
                        },
                    )()
                },
            )()
        ]
        setattr(self.choices[0], "finish_reason", finish_reason)


class FakeDeepSeekClient:
    def __init__(
        self,
        *,
        response: object | None = None,
        error: Exception | None = None,
        outcomes: list[object] | None = None,
    ) -> None:
        if outcomes is not None:
            self._outcomes = list(outcomes)
        elif error is not None:
            self._outcomes = [error]
        else:
            self._outcomes = [response]
        self.calls: list[dict[str, object]] = []
        self.options: list[dict[str, object]] = []
        self.chat = type(
            "FakeChat",
            (),
            {
                "completions": type(
                    "FakeCompletions",
                    (),
                    {"create": self._create},
                )()
            },
        )()

    def with_options(self, **kwargs: object) -> "FakeDeepSeekClient":
        self.options.append(kwargs)
        return self

    def _create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        outcome = self._outcomes.pop(0) if self._outcomes else None
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def assert_timeout_option(
    option_kwargs: dict[str, object],
    *,
    expected_total_seconds: float,
) -> None:
    timeout = option_kwargs.get("timeout")
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == min(expected_total_seconds, 10.0)
    assert timeout.read == expected_total_seconds
    assert timeout.write == min(expected_total_seconds, 30.0)
    assert timeout.pool == expected_total_seconds


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


def test_deepseek_adapter_returns_typed_success() -> None:
    fake_client = FakeDeepSeekClient(
        response=FakeDeepSeekResponse(
            content='{"summary": "ok"}',
            parsed={"summary": "ok"},
        )
    )
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(build_request(provider_id="provider-deepseek", model_id="deepseek-chat"))

    assert isinstance(result, ProviderExecutionSuccess)
    assert result.providerId == "provider-deepseek"
    assert result.modelId == "deepseek-chat"
    assert result.requestId == "req_20260326_001"
    assert result.providerRequestId == "deepseek-request-001"
    assert result.durationMs >= 0
    assert result.rawText == '{"summary": "ok"}'
    assert dict(result.rawJson) == {"summary": "ok"}
    assert len(fake_client.options) == 1
    assert fake_client.options[0]["max_retries"] == 0
    assert_timeout_option(fake_client.options[0], expected_total_seconds=3.0)
    assert fake_client.calls == [
        {
            "messages": [{"role": "user", "content": "请输出结构化分析"}],
            "model": "deepseek-chat",
            "response_format": {"type": "json_object"},
        }
    ]


def test_deepseek_adapter_maps_failure_modes() -> None:
    cases = [
        (
            httpx.HTTPStatusError(
                "server error",
                request=httpx.Request("POST", "https://api.deepseek.com/chat/completions"),
                response=httpx.Response(503, headers={"x-request-id": "status-req-001"}),
            ),
            ProviderFailureType.PROVIDER_FAILURE,
            ErrorCode.PROVIDER_FAILURE,
            True,
            "status-req-001",
        ),
        (
            httpx.HTTPStatusError(
                "unauthorized",
                request=httpx.Request("POST", "https://api.deepseek.com/chat/completions"),
                response=httpx.Response(401, headers={"x-request-id": "status-req-401"}),
            ),
            ProviderFailureType.PROVIDER_FAILURE,
            ErrorCode.PROVIDER_FAILURE,
            False,
            "status-req-401",
        ),
        (
            httpx.TimeoutException("timeout"),
            ProviderFailureType.TIMEOUT,
            ErrorCode.TIMEOUT,
            True,
            None,
        ),
        (
            ModuleNotFoundError("openai"),
            ProviderFailureType.DEPENDENCY_UNAVAILABLE,
            ErrorCode.DEPENDENCY_UNAVAILABLE,
            False,
            None,
        ),
        (
            FakeDeepSeekResponse(content="[1, 2, 3]", request_id="deepseek-request-001"),
            ProviderFailureType.CONTRACT_INVALID,
            ErrorCode.CONTRACT_INVALID,
            False,
            "deepseek-request-001",
        ),
    ]

    for outcome, failure_type, error_code, retryable, provider_request_id in cases:
        fake_client = FakeDeepSeekClient(
            response=outcome if not isinstance(outcome, Exception) else None,
            error=outcome if isinstance(outcome, Exception) else None,
        )
        adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

        result = adapter.execute(build_request(provider_id="provider-deepseek", model_id="deepseek-chat"))

        assert isinstance(result, ProviderExecutionFailure)
        assert result.failureType is failure_type
        assert map_failure_type_to_error_code(result.failureType) is error_code
        assert result.retryable is retryable
        assert result.providerRequestId == provider_request_id
        assert result.durationMs >= 0


def test_deepseek_adapter_rejects_mismatched_provider_identity() -> None:
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=FakeDeepSeekClient())

    result = adapter.execute(build_request(provider_id="provider-other", model_id="model-other"))

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.CONTRACT_INVALID
    assert result.providerId == "provider-deepseek"
    assert result.modelId == "deepseek-chat"
    assert result.retryable is False
    assert result.providerRequestId is None


def test_deepseek_adapter_reads_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "env-key")

    adapter = DeepSeekProviderAdapter(client=FakeDeepSeekClient(response=FakeDeepSeekResponse()))

    assert adapter.api_key == "env-key"


def test_deepseek_adapter_without_api_key_maps_to_dependency_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    adapter = DeepSeekProviderAdapter(client=FakeDeepSeekClient(response=FakeDeepSeekResponse()))

    result = adapter.execute(build_request(provider_id="provider-deepseek", model_id="deepseek-chat"))

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.DEPENDENCY_UNAVAILABLE
    assert result.retryable is False
    assert result.providerRequestId is None


def test_deepseek_adapter_hides_api_key_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "env-key")

    adapter = DeepSeekProviderAdapter(client=FakeDeepSeekClient(response=FakeDeepSeekResponse()))

    assert "env-key" not in repr(adapter)


def test_deepseek_adapter_returns_deeply_frozen_raw_json() -> None:
    adapter = DeepSeekProviderAdapter(
        api_key="test-key",
        client=FakeDeepSeekClient(
            response=FakeDeepSeekResponse(
                content='{"summary": {"score": 95}, "items": [{"label": "ok"}]}',
                parsed={"summary": {"score": 95}, "items": [{"label": "ok"}]},
            )
        ),
    )

    result = adapter.execute(build_request(provider_id="provider-deepseek", model_id="deepseek-chat"))

    assert isinstance(result, ProviderExecutionSuccess)
    with pytest.raises(TypeError):
        result.rawJson["summary"]["score"] = 90
    with pytest.raises(TypeError):
        result.rawJson["items"][0]["label"] = "changed"


def test_deepseek_adapter_reraises_unknown_exceptions() -> None:
    adapter = DeepSeekProviderAdapter(
        api_key="test-key",
        client=FakeDeepSeekClient(error=RuntimeError("unexpected")),
    )

    with pytest.raises(RuntimeError, match="unexpected"):
        adapter.execute(build_request(provider_id="provider-deepseek", model_id="deepseek-chat"))


def test_deepseek_adapter_rejects_response_format_with_extra_fields() -> None:
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=FakeDeepSeekClient(response=FakeDeepSeekResponse()))

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            response_format={"type": "json_object", "schema": "ignored"},
        )
    )

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.CONTRACT_INVALID
    assert result.retryable is False
    assert result.providerRequestId is None


def test_deepseek_adapter_supports_string_response_format() -> None:
    fake_client = FakeDeepSeekClient(response=FakeDeepSeekResponse(parsed={"summary": "ok"}))
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            response_format="json_object",
        )
    )

    assert isinstance(result, ProviderExecutionSuccess)
    assert fake_client.calls == [
        {
            "messages": [{"role": "user", "content": "请输出结构化分析"}],
            "model": "deepseek-chat",
            "response_format": {"type": "json_object"},
        }
    ]


def test_deepseek_adapter_omits_response_format_when_not_provided() -> None:
    fake_client = FakeDeepSeekClient(response=FakeDeepSeekResponse(parsed={"summary": "ok"}))
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            response_format=None,
        )
    )

    assert isinstance(result, ProviderExecutionSuccess)
    assert fake_client.calls == [
        {
            "messages": [{"role": "user", "content": "请输出结构化分析"}],
            "model": "deepseek-chat",
        }
    ]


def test_deepseek_adapter_passes_timeout_and_max_tokens() -> None:
    fake_client = FakeDeepSeekClient(response=FakeDeepSeekResponse(parsed={"summary": "ok"}))
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            timeout_ms=90_000,
            max_tokens=1_500,
            response_format="json_object",
        )
    )

    assert isinstance(result, ProviderExecutionSuccess)
    assert len(fake_client.options) == 1
    assert fake_client.options[0]["max_retries"] == 0
    assert_timeout_option(fake_client.options[0], expected_total_seconds=90.0)
    assert fake_client.calls == [
        {
            "messages": [{"role": "user", "content": "请输出结构化分析"}],
            "max_tokens": 1500,
            "model": "deepseek-chat",
            "response_format": {"type": "json_object"},
        }
    ]


def test_deepseek_adapter_retries_empty_json_content_once_and_succeeds() -> None:
    fake_client = FakeDeepSeekClient(
        outcomes=[
            FakeDeepSeekResponse(content="", request_id="deepseek-request-001"),
            FakeDeepSeekResponse(content='{"summary": "ok"}', request_id="deepseek-request-002"),
        ]
    )
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            response_format="json_object",
        )
    )

    assert isinstance(result, ProviderExecutionSuccess)
    assert result.providerRequestId == "deepseek-request-002"
    assert len(fake_client.calls) == 2
    assert len(fake_client.options) == 2
    for option_kwargs in fake_client.options:
        assert option_kwargs["max_retries"] == 0
        assert_timeout_option(option_kwargs, expected_total_seconds=3.0)


def test_deepseek_adapter_disables_sdk_retries_even_without_explicit_timeout() -> None:
    fake_client = FakeDeepSeekClient(response=FakeDeepSeekResponse(parsed={"summary": "ok"}))
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            timeout_ms=None,
            response_format="json_object",
        )
    )

    assert isinstance(result, ProviderExecutionSuccess)
    assert fake_client.options == [{"max_retries": 0}]


def test_deepseek_adapter_retries_invalid_json_once_then_returns_provider_failure() -> None:
    fake_client = FakeDeepSeekClient(
        outcomes=[
            FakeDeepSeekResponse(content='{"summary":', request_id="deepseek-request-001", finish_reason="length"),
            FakeDeepSeekResponse(content='{"summary":', request_id="deepseek-request-002", finish_reason="length"),
        ]
    )
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            response_format="json_object",
        )
    )

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.PROVIDER_FAILURE
    assert result.retryable is True
    assert result.providerRequestId == "deepseek-request-002"
    assert "max_tokens" in result.message
    assert len(fake_client.calls) == 2


def test_deepseek_adapter_retries_non_json_once_then_returns_provider_failure() -> None:
    fake_client = FakeDeepSeekClient(
        outcomes=[
            FakeDeepSeekResponse(content="not-json", request_id="deepseek-request-001"),
            FakeDeepSeekResponse(content="still-not-json", request_id="deepseek-request-002"),
        ]
    )
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            response_format="json_object",
        )
    )

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.PROVIDER_FAILURE
    assert result.retryable is True
    assert result.providerRequestId == "deepseek-request-002"
    assert "合法 JSON" in result.message
    assert len(fake_client.calls) == 2


def test_deepseek_adapter_accepts_text_response_format_with_plain_text() -> None:
    fake_client = FakeDeepSeekClient(response=FakeDeepSeekResponse(content="纯文本响应", parsed=None))
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=fake_client)

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            response_format="text",
        )
    )

    assert isinstance(result, ProviderExecutionSuccess)
    assert result.rawText == "纯文本响应"
    assert result.rawJson == "纯文本响应"
    assert fake_client.calls == [
        {
            "messages": [{"role": "user", "content": "请输出结构化分析"}],
            "model": "deepseek-chat",
            "response_format": {"type": "text"},
        }
    ]


def test_deepseek_adapter_rejects_non_object_json_for_json_object_response_format() -> None:
    adapter = DeepSeekProviderAdapter(
        api_key="test-key",
        client=FakeDeepSeekClient(response=FakeDeepSeekResponse(content="[1, 2, 3]")),
    )

    result = adapter.execute(
        build_request(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            response_format={"type": "json_object"},
        )
    )

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.CONTRACT_INVALID
    assert result.retryable is False
    assert result.providerRequestId == "deepseek-request-001"


def test_deepseek_adapter_maps_openai_status_subclass_exceptions() -> None:
    authentication_error = type(
        "AuthenticationError",
        (Exception,),
        {"__module__": "openai._exceptions", "status_code": 401},
    )("unauthorized")
    adapter = DeepSeekProviderAdapter(api_key="test-key", client=FakeDeepSeekClient(error=authentication_error))

    result = adapter.execute(build_request(provider_id="provider-deepseek", model_id="deepseek-chat"))

    assert isinstance(result, ProviderExecutionFailure)
    assert result.failureType is ProviderFailureType.PROVIDER_FAILURE
    assert result.retryable is False


def test_deepseek_adapter_rejects_non_official_base_url() -> None:
    with pytest.raises(ValueError, match="官方 API 域名"):
        DeepSeekProviderAdapter(api_key="test-key", base_url="https://evil.example.com")


def test_deepseek_adapter_rejects_non_default_official_port() -> None:
    with pytest.raises(ValueError, match="官方 API 域名"):
        DeepSeekProviderAdapter(api_key="test-key", base_url="https://api.deepseek.com:8443")
