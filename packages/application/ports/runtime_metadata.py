from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from provider_adapters import ProviderExecutionRequest, ProviderExecutionResult


@dataclass(frozen=True, slots=True)
class RuntimeMetadata:
    schema_version: str
    prompt_version: str
    rubric_version: str
    provider_id: str
    model_id: str


class ResolvedPromptPort(Protocol):
    promptId: str
    promptVersion: str
    schemaVersion: str
    rubricVersion: str
    body: str


class PromptRuntimePort(Protocol):
    def resolve(
        self,
        *,
        stage: str,
        input_composition: str,
        evaluation_mode: str,
        provider_id: str,
        model_id: str,
    ) -> ResolvedPromptPort:
        ...


class ProviderMetadataPort(Protocol):
    provider_id: str
    model_id: str


class ProviderExecutionPort(ProviderMetadataPort, Protocol):
    def execute(self, request: ProviderExecutionRequest) -> ProviderExecutionResult:
        ...


@dataclass(frozen=True, slots=True)
class StaticResolvedPrompt:
    promptId: str = "prompt-default"
    promptVersion: str = "prompt-v1"
    schemaVersion: str = "1.0.0"
    rubricVersion: str = "rubric-v1"
    body: str = "You are the default prompt placeholder."


@dataclass(frozen=True, slots=True)
class StaticPromptRuntime:
    resolved_prompt: StaticResolvedPrompt = StaticResolvedPrompt()

    def resolve(
        self,
        *,
        stage: str,
        input_composition: str,
        evaluation_mode: str,
        provider_id: str,
        model_id: str,
    ) -> StaticResolvedPrompt:
        return self.resolved_prompt


@dataclass(frozen=True, slots=True)
class StaticProviderMetadata:
    provider_id: str = "provider-deepseek"
    model_id: str = "deepseek-chat"
