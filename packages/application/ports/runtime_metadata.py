from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RuntimeMetadata:
    schema_version: str
    prompt_version: str
    rubric_version: str
    provider_id: str
    model_id: str


class ResolvedPromptPort(Protocol):
    promptVersion: str
    schemaVersion: str
    rubricVersion: str


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


@dataclass(frozen=True, slots=True)
class StaticResolvedPrompt:
    promptVersion: str = "prompt-v1"
    schemaVersion: str = "1.0.0"
    rubricVersion: str = "rubric-v1"


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
    provider_id: str = "provider-local"
    model_id: str = "model-local"
