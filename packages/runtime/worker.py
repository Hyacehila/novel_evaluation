from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.schemas.common.enums import AnalysisMode, InputComposition
from packages.runtime.logging import configure_process_logging
from packages.runtime.service_factory import RuntimePromptRuntime, get_startup_provider_adapter, resolve_prompts_root

_DEEPSEEK_API_KEY_ENV = "NOVEL_EVAL_DEEPSEEK_API_KEY"
_DEEPSEEK_MODEL_ID_ENV = "NOVEL_EVAL_DEEPSEEK_MODEL_ID"
_PROVIDER_ID = "provider-deepseek"
_DEFAULT_DEEPSEEK_MODEL_ID = "deepseek-v4-pro"
_ALLOWED_DEEPSEEK_MODEL_IDS = frozenset({"deepseek-v4-flash", "deepseek-v4-pro"})


def _read_deepseek_model_id() -> str:
    raw_value = os.getenv(_DEEPSEEK_MODEL_ID_ENV)
    if raw_value is None:
        return _DEFAULT_DEEPSEEK_MODEL_ID
    normalized = raw_value.strip()
    if not normalized:
        return _DEFAULT_DEEPSEEK_MODEL_ID
    if normalized not in _ALLOWED_DEEPSEEK_MODEL_IDS:
        allowed = ", ".join(sorted(_ALLOWED_DEEPSEEK_MODEL_IDS))
        raise RuntimeError(f"{_DEEPSEEK_MODEL_ID_ENV} 只支持：{allowed}。")
    return normalized


_MODEL_ID = _read_deepseek_model_id()


@dataclass(frozen=True, slots=True)
class WorkerRuntimeMetadata:
    schema_version: str
    prompt_version: str
    rubric_version: str
    provider_id: str
    model_id: str


@dataclass(frozen=True, slots=True)
class WorkerRuntimeContext:
    command_name: str
    repo_root: Path
    evals_root: Path
    prompts_root: Path
    prompt_runtime: RuntimePromptRuntime
    provider_adapter: ProviderExecutionPort
    runtime_metadata: WorkerRuntimeMetadata
    api_handoff_enabled: bool = False
    real_execution_enabled: bool = True


@dataclass(frozen=True, slots=True)
class DryRunProviderAdapter:
    provider_id: str = _PROVIDER_ID
    model_id: str = _MODEL_ID

    def execute(self, request):
        raise RuntimeError("worker dry-run runtime does not execute provider requests.")


def bootstrap_worker_runtime(*, command_name: str, dry_run: bool = False) -> WorkerRuntimeContext:
    repo_root = Path(__file__).resolve().parents[2]
    configure_process_logging(service_name="worker", repo_root=repo_root)
    prompts_root = resolve_prompts_root()
    evals_root = repo_root / "evals"
    prompt_runtime = RuntimePromptRuntime()
    startup_key = _read_startup_provider_key()
    real_execution_enabled = startup_key is not None
    provider_adapter = (
        get_startup_provider_adapter()
        if real_execution_enabled or not dry_run
        else DryRunProviderAdapter()
    )
    resolved_prompt = prompt_runtime.resolve(
        stage="input_screening",
        input_composition=InputComposition.CHAPTERS_OUTLINE.value,
        analysis_mode=AnalysisMode.LONG_OPENING_OUTLINE.value,
        provider_id=provider_adapter.provider_id,
        model_id=provider_adapter.model_id,
    )
    return WorkerRuntimeContext(
        command_name=command_name,
        repo_root=repo_root,
        evals_root=evals_root,
        prompts_root=prompts_root,
        prompt_runtime=prompt_runtime,
        provider_adapter=provider_adapter,
        runtime_metadata=WorkerRuntimeMetadata(
            schema_version=resolved_prompt.schemaVersion,
            prompt_version=resolved_prompt.promptVersion,
            rubric_version=resolved_prompt.rubricVersion,
            provider_id=provider_adapter.provider_id,
            model_id=provider_adapter.model_id,
        ),
        real_execution_enabled=real_execution_enabled,
    )


def _read_startup_provider_key() -> str | None:
    raw_value = os.getenv(_DEEPSEEK_API_KEY_ENV)
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    return normalized or None
