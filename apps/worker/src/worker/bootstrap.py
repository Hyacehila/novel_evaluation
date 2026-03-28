from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from api.dependencies import ApiPromptRuntime, get_startup_provider_adapter, resolve_prompts_root
from packages.application.ports.runtime_metadata import ProviderExecutionPort
from packages.application.support.process_logging import configure_process_logging
from packages.schemas.common.enums import EvaluationMode, InputComposition


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
    prompt_runtime: ApiPromptRuntime
    provider_adapter: ProviderExecutionPort
    runtime_metadata: WorkerRuntimeMetadata
    api_handoff_enabled: bool = False
    real_execution_enabled: bool = True


def bootstrap_worker_runtime(*, command_name: str) -> WorkerRuntimeContext:
    repo_root = Path(__file__).resolve().parents[4]
    configure_process_logging(service_name="worker", repo_root=repo_root)
    prompts_root = resolve_prompts_root()
    evals_root = repo_root / "evals"
    prompt_runtime = ApiPromptRuntime()
    provider_adapter = get_startup_provider_adapter()
    resolved_prompt = prompt_runtime.resolve(
        stage="input_screening",
        input_composition=InputComposition.CHAPTERS_OUTLINE.value,
        evaluation_mode=EvaluationMode.FULL.value,
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
    )
