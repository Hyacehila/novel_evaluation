from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkerRuntimeMetadata:
    schema_version: str = "unwired"
    prompt_version: str = "unwired"
    rubric_version: str = "unwired"
    provider_id: str = "unwired"
    model_id: str = "unwired"


@dataclass(frozen=True, slots=True)
class WorkerRuntimeContext:
    command_name: str
    runtime_metadata: WorkerRuntimeMetadata = WorkerRuntimeMetadata()
    api_handoff_enabled: bool = False
    real_execution_enabled: bool = False


def bootstrap_worker_runtime(*, command_name: str) -> WorkerRuntimeContext:
    return WorkerRuntimeContext(command_name=command_name)
