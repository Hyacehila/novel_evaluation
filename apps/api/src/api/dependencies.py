from __future__ import annotations

import os
import sys
from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from packages.application.ports.runtime_metadata import StaticPromptRuntime, StaticResolvedPrompt
from packages.application.services.evaluation_service import EvaluationService
from packages.schemas.common.enums import EvaluationMode, InputComposition

from .sqlite_repository import SQLiteTaskRepository, resolve_db_path

REPO_ROOT = Path(__file__).resolve().parents[4]
PROMPTS_ROOT = REPO_ROOT / "prompts"
PROMPT_RUNTIME_PACKAGE_DIR = REPO_ROOT / "packages" / "prompt-runtime" / "src" / "prompt_runtime"
PROVIDER_ADAPTERS_PACKAGE_DIR = REPO_ROOT / "packages" / "provider-adapters" / "src" / "provider_adapters"
PROMPT_RUNTIME_MODULE_NAME = "api._prompt_runtime_runtime"
PROVIDER_ADAPTERS_MODULE_NAME = "api._provider_adapters_runtime"
PRIMARY_PROMPT_RUNTIME_SCOPES = frozenset(
    {
        (
            InputComposition.CHAPTERS_OUTLINE.value,
            EvaluationMode.FULL.value,
            "provider-local",
            "model-local",
        )
    }
)



def _load_package(*, module_name: str, package_dir: Path) -> ModuleType:
    init_path = package_dir / "__init__.py"
    if not init_path.exists():
        raise ImportError(f"包入口不存在：{init_path}")
    spec = spec_from_file_location(
        module_name,
        init_path,
        submodule_search_locations=[str(package_dir)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载包：{package_dir}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


@lru_cache(maxsize=1)
def _get_prompt_runtime_module() -> ModuleType:
    return _load_package(module_name=PROMPT_RUNTIME_MODULE_NAME, package_dir=PROMPT_RUNTIME_PACKAGE_DIR)


@lru_cache(maxsize=1)
def _get_provider_adapters_module() -> ModuleType:
    return _load_package(module_name=PROVIDER_ADAPTERS_MODULE_NAME, package_dir=PROVIDER_ADAPTERS_PACKAGE_DIR)


class ApiPromptRuntime:
    def __init__(self) -> None:
        prompt_runtime_module = _get_prompt_runtime_module()
        self._file_runtime = prompt_runtime_module.FilePromptRuntime(prompts_root=PROMPTS_ROOT)
        self._fallback_runtime = StaticPromptRuntime(
            resolved_prompt=StaticResolvedPrompt(
                promptVersion="v1",
                schemaVersion="1.0.0",
                rubricVersion="rubric-v1",
            )
        )

    def resolve(
        self,
        *,
        stage: str,
        input_composition: str,
        evaluation_mode: str,
        provider_id: str,
        model_id: str,
    ):
        scope = (input_composition, evaluation_mode, provider_id, model_id)
        if scope in PRIMARY_PROMPT_RUNTIME_SCOPES:
            return self._file_runtime.resolve(
                stage=stage,
                input_composition=input_composition,
                evaluation_mode=evaluation_mode,
                provider_id=provider_id,
                model_id=model_id,
            )
        return self._fallback_runtime.resolve(
            stage=stage,
            input_composition=input_composition,
            evaluation_mode=evaluation_mode,
            provider_id=provider_id,
            model_id=model_id,
        )


@lru_cache(maxsize=1)
def get_task_repository() -> SQLiteTaskRepository:
    db_path = resolve_db_path(os.getenv("NOVEL_EVAL_DB_PATH"))
    return SQLiteTaskRepository(db_path=db_path)


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    provider_adapters_module = _get_provider_adapters_module()
    return EvaluationService(
        task_repository=get_task_repository(),
        prompt_runtime=ApiPromptRuntime(),
        provider_adapter=provider_adapters_module.LocalDeterministicProviderAdapter(),
    )



def recover_processing_tasks() -> None:
    service = get_evaluation_service()
    service.recover_incomplete_tasks()
