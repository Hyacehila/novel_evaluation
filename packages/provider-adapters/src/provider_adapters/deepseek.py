from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from .contracts import (
    ProviderExecutionFailure,
    ProviderExecutionRequest,
    ProviderExecutionResult,
    ProviderExecutionSuccess,
    ProviderFailureType,
    build_provider_failure,
)

_DEEPSEEK_API_KEY_ENV = "NOVEL_EVAL_DEEPSEEK_API_KEY"
_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_ALLOWED_DEEPSEEK_BASE_PATHS = frozenset({"", "/v1"})
_OPENAI_EXCEPTION_MODULE_ROOT = "openai"
_OPENAI_TIMEOUT_ERROR_NAMES = frozenset({"APITimeoutError"})
_OPENAI_STATUS_ERROR_NAMES = frozenset({"APIStatusError", "RateLimitError"})
_OPENAI_CONNECTION_ERROR_NAMES = frozenset({"APIConnectionError"})
_RETRYABLE_PROVIDER_STATUS_CODES = frozenset({408, 429})
_CONNECT_TIMEOUT_CAP_SECONDS = 10.0
_WRITE_TIMEOUT_CAP_SECONDS = 30.0


class DeepSeekResponseHandlingError(Exception):
    def __init__(
        self,
        *,
        failure_type: ProviderFailureType,
        message: str,
        retryable: bool | None,
        can_retry: bool,
    ) -> None:
        super().__init__(message)
        self.failure_type = failure_type
        self.message = message
        self.retryable = retryable
        self.can_retry = can_retry


class DeepSeekChatCompletionsProtocol(Protocol):
    def create(self, **kwargs: Any) -> Any:
        ...


class DeepSeekChatProtocol(Protocol):
    completions: DeepSeekChatCompletionsProtocol


class DeepSeekClientProtocol(Protocol):
    chat: DeepSeekChatProtocol

    def with_options(self, **kwargs: Any) -> DeepSeekClientProtocol:
        ...


@dataclass(frozen=True, slots=True)
class DeepSeekProviderAdapter:
    api_key: str | None = field(default=None, repr=False)
    provider_id: str = "provider-deepseek"
    model_id: str = "deepseek-chat"
    base_url: str = _DEEPSEEK_BASE_URL
    client: DeepSeekClientProtocol | None = None
    _client_factory: Any | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "api_key", self.api_key or os.getenv(_DEEPSEEK_API_KEY_ENV))
        self._validate_base_url()

    def execute(self, request: ProviderExecutionRequest) -> ProviderExecutionResult:
        started_at = perf_counter()

        if request.providerId != self.provider_id or request.modelId != self.model_id:
            return self._build_failure(
                request=request,
                duration_ms=self._duration_ms(started_at),
                failure_type=ProviderFailureType.CONTRACT_INVALID,
                message="DeepSeek adapter 收到与自身不匹配的 providerId 或 modelId。",
            )

        if not self.api_key:
            return self._build_failure(
                request=request,
                duration_ms=self._duration_ms(started_at),
                failure_type=ProviderFailureType.DEPENDENCY_UNAVAILABLE,
                message="缺少 DeepSeek API Key 配置。",
                retryable=False,
            )

        response: Any | None = None
        response_type = self._resolve_response_type(request.responseFormat)
        try:
            client = self.client or self._build_client()
            payload = self._build_payload(request)
        except (ImportError, ModuleNotFoundError):
            return self._build_failure(
                request=request,
                duration_ms=self._duration_ms(started_at),
                failure_type=ProviderFailureType.DEPENDENCY_UNAVAILABLE,
                message="DeepSeek SDK 不可用。",
                retryable=False,
            )
        except ValueError:
            return self._build_failure(
                request=request,
                duration_ms=self._duration_ms(started_at),
                failure_type=ProviderFailureType.CONTRACT_INVALID,
                message="DeepSeek 请求不满足 provider contract。",
                retryable=False,
            )

        max_attempts = 2 if response_type == "json_object" else 1
        for attempt in range(max_attempts):
            try:
                response = self._create_completion(client=client, payload=payload, request=request)
            except (ImportError, ModuleNotFoundError):
                return self._build_failure(
                    request=request,
                    duration_ms=self._duration_ms(started_at),
                    failure_type=ProviderFailureType.DEPENDENCY_UNAVAILABLE,
                    message="DeepSeek SDK 不可用。",
                    retryable=False,
                )
            except Exception as exc:
                failure_type = self._map_known_exception_to_failure_type(exc)
                if failure_type is None:
                    raise
                return self._build_failure(
                    request=request,
                    duration_ms=self._duration_ms(started_at),
                    failure_type=failure_type,
                    message=self._build_exception_message(exc, failure_type),
                    provider_request_id=self._extract_provider_request_id(getattr(exc, "response", response)),
                    retryable=self._resolve_retryable(exc, failure_type),
                )

            try:
                provider_request_id = self._extract_provider_request_id(response)
                raw_text = self._extract_raw_text(response, response_type=response_type)
                raw_json = self._extract_raw_json(response, raw_text, response_type=response_type)
                self._validate_response_contract(request=request, raw_json=raw_json)
                return ProviderExecutionSuccess(
                    providerId=self.provider_id,
                    modelId=self.model_id,
                    requestId=request.requestId,
                    providerRequestId=provider_request_id,
                    durationMs=self._duration_ms(started_at),
                    rawText=raw_text,
                    rawJson=raw_json,
                )
            except DeepSeekResponseHandlingError as exc:
                if exc.can_retry and attempt + 1 < max_attempts:
                    continue
                return self._build_failure(
                    request=request,
                    duration_ms=self._duration_ms(started_at),
                    failure_type=exc.failure_type,
                    message=exc.message,
                    provider_request_id=self._extract_provider_request_id(response),
                    retryable=exc.retryable,
                )
            except ValueError:
                return self._build_failure(
                    request=request,
                    duration_ms=self._duration_ms(started_at),
                    failure_type=ProviderFailureType.CONTRACT_INVALID,
                    message="DeepSeek 响应不满足 provider contract。",
                    provider_request_id=self._extract_provider_request_id(response),
                )

        return self._build_failure(
            request=request,
            duration_ms=self._duration_ms(started_at),
            failure_type=ProviderFailureType.PROVIDER_FAILURE,
            message="DeepSeek 响应未能在允许的尝试次数内完成。",
            provider_request_id=self._extract_provider_request_id(response),
            retryable=True,
        )

    def _build_client(self) -> DeepSeekClientProtocol:
        if self._client_factory is not None:
            return self._client_factory(api_key=self.api_key, base_url=self.base_url)
        from openai import OpenAI

        return OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)

    def _create_completion(
        self,
        *,
        client: DeepSeekClientProtocol,
        payload: dict[str, Any],
        request: ProviderExecutionRequest,
    ) -> Any:
        selected_client = client
        if hasattr(client, "with_options"):
            option_kwargs: dict[str, Any] = {"max_retries": 0}
            if request.timeoutMs is not None:
                option_kwargs["timeout"] = self._build_timeout(request.timeoutMs)
            selected_client = client.with_options(**option_kwargs)
        return selected_client.chat.completions.create(**payload)

    def _build_timeout(self, timeout_ms: int) -> httpx.Timeout:
        total_seconds = max(timeout_ms / 1000, 1.0)
        return httpx.Timeout(
            timeout=total_seconds,
            connect=min(total_seconds, _CONNECT_TIMEOUT_CAP_SECONDS),
            read=total_seconds,
            write=min(total_seconds, _WRITE_TIMEOUT_CAP_SECONDS),
            pool=total_seconds,
        )

    def _build_payload(self, request: ProviderExecutionRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": [{"role": message.role, "content": message.content} for message in request.messages],
        }
        if request.maxTokens is not None:
            payload["max_tokens"] = request.maxTokens
        if request.responseFormat is not None:
            payload["response_format"] = self._normalize_response_format(request.responseFormat)
        return payload

    def _normalize_response_format(self, response_format: str | dict[str, Any]) -> dict[str, str]:
        if isinstance(response_format, str):
            normalized = {"type": response_format}
        else:
            extra_keys = set(response_format) - {"type"}
            if extra_keys:
                raise ValueError("responseFormat 包含未支持字段。")
            normalized = {"type": response_format.get("type")}
        response_type = normalized.get("type")
        if response_type not in {"text", "json_object"}:
            raise ValueError("responseFormat.type 不受支持。")
        return {"type": response_type}

    def _map_known_exception_to_failure_type(self, exc: Exception) -> ProviderFailureType | None:
        name = exc.__class__.__name__
        module = exc.__class__.__module__
        if isinstance(exc, httpx.TimeoutException) or name in _OPENAI_TIMEOUT_ERROR_NAMES:
            return ProviderFailureType.TIMEOUT
        if isinstance(exc, httpx.HTTPStatusError) or name in _OPENAI_STATUS_ERROR_NAMES:
            return ProviderFailureType.PROVIDER_FAILURE
        if isinstance(exc, httpx.HTTPError) or name in _OPENAI_CONNECTION_ERROR_NAMES:
            return ProviderFailureType.DEPENDENCY_UNAVAILABLE
        if not module.startswith(_OPENAI_EXCEPTION_MODULE_ROOT):
            return None
        if hasattr(exc, "status_code") or getattr(exc, "response", None) is not None:
            return ProviderFailureType.PROVIDER_FAILURE
        return None

    def _build_exception_message(self, exc: Exception, failure_type: ProviderFailureType) -> str:
        if failure_type is ProviderFailureType.TIMEOUT:
            return "DeepSeek 请求超时。"
        if failure_type is ProviderFailureType.PROVIDER_FAILURE:
            status_code = self._extract_status_code(exc)
            if status_code is None:
                return "DeepSeek 返回异常状态。"
            return f"DeepSeek 返回异常状态码 {status_code}。"
        return "DeepSeek 依赖不可用。"

    def _resolve_retryable(self, exc: Exception, failure_type: ProviderFailureType) -> bool | None:
        if failure_type is ProviderFailureType.PROVIDER_FAILURE:
            status_code = self._extract_status_code(exc)
            if status_code is None:
                return True
            return status_code >= 500 or status_code in _RETRYABLE_PROVIDER_STATUS_CODES
        return None

    def _extract_status_code(self, exc: Exception) -> int | None:
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int):
            return status_code
        response = getattr(exc, "response", None)
        response_status_code = getattr(response, "status_code", None)
        if isinstance(response_status_code, int):
            return response_status_code
        return None

    def _extract_provider_request_id(self, response: Any) -> str | None:
        if response is None:
            return None
        response_id = getattr(response, "id", None)
        if isinstance(response_id, str) and response_id.strip():
            return response_id
        request_id = getattr(response, "request_id", None)
        if isinstance(request_id, str) and request_id.strip():
            return request_id
        headers = getattr(response, "headers", None)
        if headers is None:
            return None
        header_id = headers.get("x-request-id") or headers.get("X-Request-Id")
        if isinstance(header_id, str) and header_id.strip():
            return header_id
        return None

    def _extract_raw_text(self, response: Any, *, response_type: str | None) -> str:
        choices = getattr(response, "choices", None)
        if not choices:
            raise ValueError("响应缺少 choices。")
        message = getattr(choices[0], "message", None)
        if message is None:
            raise ValueError("响应缺少 message。")
        content = getattr(message, "content", None)
        if response_type == "json_object" and (not isinstance(content, str) or not content.strip()):
            raise DeepSeekResponseHandlingError(
                failure_type=ProviderFailureType.PROVIDER_FAILURE,
                message="DeepSeek JSON 输出返回空 content。",
                retryable=True,
                can_retry=True,
            )
        if not isinstance(content, str) or not content.strip():
            raise ValueError("响应 message.content 为空。")
        return content

    def _extract_raw_json(self, response: Any, raw_text: str, *, response_type: str | None) -> Any:
        choices = getattr(response, "choices", None)
        message = getattr(choices[0], "message", None)
        parsed = getattr(message, "parsed", None)
        if parsed is not None:
            if hasattr(parsed, "model_dump"):
                return parsed.model_dump(mode="json")
            if isinstance(parsed, dict | list | tuple | str | int | float | bool):
                return parsed
            raise ValueError("响应 parsed 字段不是合法 JSON 风格结构。")
        if response_type == "text":
            return raw_text
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as exc:
            if response_type == "json_object":
                message = "DeepSeek JSON 输出不是合法 JSON。"
                if self._response_maybe_truncated(response):
                    message = "DeepSeek JSON 输出因长度截断，max_tokens 可能不足。"
                raise DeepSeekResponseHandlingError(
                    failure_type=ProviderFailureType.PROVIDER_FAILURE,
                    message=message,
                    retryable=True,
                    can_retry=True,
                ) from exc
            raise ValueError("响应正文不是合法 JSON。") from exc

    def _resolve_response_type(self, response_format: str | dict[str, Any] | None) -> str | None:
        if isinstance(response_format, str):
            return response_format
        if isinstance(response_format, dict):
            return response_format.get("type")
        return None

    def _validate_response_contract(self, *, request: ProviderExecutionRequest, raw_json: Any) -> None:
        response_type = self._resolve_response_type(request.responseFormat)
        if response_type == "json_object" and not isinstance(raw_json, Mapping):
            raise DeepSeekResponseHandlingError(
                failure_type=ProviderFailureType.CONTRACT_INVALID,
                message="DeepSeek JSON 输出必须返回对象。",
                retryable=False,
                can_retry=False,
            )

    def _response_maybe_truncated(self, response: Any) -> bool:
        choices = getattr(response, "choices", None)
        if not choices:
            return False
        finish_reason = getattr(choices[0], "finish_reason", None)
        return finish_reason == "length"

    def _validate_base_url(self) -> None:
        parsed = urlparse(self.base_url)
        normalized_path = parsed.path.rstrip("/")
        if (
            parsed.scheme != "https"
            or parsed.hostname != "api.deepseek.com"
            or parsed.port not in (None, 443)
            or normalized_path not in _ALLOWED_DEEPSEEK_BASE_PATHS
            or parsed.query
            or parsed.params
            or parsed.fragment
        ):
            raise ValueError("DeepSeek base_url 必须指向官方 API 域名。")

    def _build_failure(
        self,
        *,
        request: ProviderExecutionRequest,
        duration_ms: int,
        failure_type: ProviderFailureType,
        message: str,
        provider_request_id: str | None = None,
        retryable: bool | None = None,
    ) -> ProviderExecutionFailure:
        return build_provider_failure(
            provider_id=self.provider_id,
            model_id=self.model_id,
            request_id=request.requestId,
            provider_request_id=provider_request_id,
            duration_ms=duration_ms,
            failure_type=failure_type,
            message=message,
            retryable=retryable,
        )

    def _duration_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))
