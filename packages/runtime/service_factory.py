from __future__ import annotations

import logging
import os
import sys
import threading
from functools import lru_cache
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from packages.application.ports.runtime_metadata import (
    ProviderExecutionPort,
    ProviderRuntimeExecutionPort,
    StaticPromptRuntime,
    StaticResolvedPrompt,
)
from packages.application.services.evaluation_service import EvaluationService
from packages.schemas.common.enums import EvaluationMode, InputComposition
from packages.schemas.output.provider_status import ProviderConfigurationSource, ProviderStatus
from packages.runtime.logging import log_event
from packages.runtime.persistence import SQLiteTaskRepository, resolve_db_path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_RUNTIME_PACKAGE_DIR = REPO_ROOT / "packages" / "prompt-runtime" / "src" / "prompt_runtime"
PROVIDER_ADAPTERS_PACKAGE_DIR = REPO_ROOT / "packages" / "provider-adapters" / "src" / "provider_adapters"
PROMPT_RUNTIME_MODULE_NAME = "packages.runtime._prompt_runtime_runtime"
PROVIDER_ADAPTERS_MODULE_NAME = "packages.runtime._provider_adapters_runtime"
PRIMARY_PROMPT_RUNTIME_SCOPES = frozenset(
    {
        (
            InputComposition.CHAPTERS_OUTLINE.value,
            EvaluationMode.FULL.value,
            "provider-deepseek",
            "deepseek-chat",
        ),
        (
            InputComposition.CHAPTERS_ONLY.value,
            EvaluationMode.DEGRADED.value,
            "provider-deepseek",
            "deepseek-chat",
        ),
        (
            InputComposition.OUTLINE_ONLY.value,
            EvaluationMode.DEGRADED.value,
            "provider-deepseek",
            "deepseek-chat",
        ),
    }
)

logger = logging.getLogger(__name__)
_REQUIRE_REAL_PROVIDER_ENV = "NOVEL_EVAL_REQUIRE_REAL_PROVIDER"
_DEEPSEEK_API_KEY_ENV = "NOVEL_EVAL_DEEPSEEK_API_KEY"
_ALLOW_E2E_PROVIDER_RESET_ENV = "NOVEL_EVAL_E2E_ALLOW_PROVIDER_RESET"
_E2E_PROVIDER_MODE_ENV = "NOVEL_EVAL_E2E_PROVIDER_MODE"
_PROVIDER_ID = "provider-deepseek"
_MODEL_ID = "deepseek-chat"
_DETERMINISTIC_PROVIDER_MODE = "deterministic"


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


class RuntimePromptRuntime:
    def __init__(self) -> None:
        prompt_runtime_module = _get_prompt_runtime_module()
        self._file_runtime = prompt_runtime_module.FilePromptRuntime(prompts_root=resolve_prompts_root())
        self._fallback_runtime = StaticPromptRuntime(
            resolved_prompt=StaticResolvedPrompt(
                promptId="prompt-fallback",
                promptVersion="v1",
                schemaVersion="1.0.0",
                rubricVersion="rubric-v1",
                body="You are the fallback prompt placeholder.",
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
        try:
            return self._file_runtime.resolve(
                stage=stage,
                input_composition=input_composition,
                evaluation_mode=evaluation_mode,
                provider_id=provider_id,
                model_id=model_id,
            )
        except Exception:
            if provider_id == _PROVIDER_ID and model_id == _MODEL_ID:
                raise
            return self._fallback_runtime.resolve(
                stage=stage,
                input_composition=input_composition,
                evaluation_mode=evaluation_mode,
                provider_id=provider_id,
                model_id=model_id,
            )


class ProviderRuntimeState:
    provider_id = _PROVIDER_ID
    model_id = _MODEL_ID

    def __init__(self) -> None:
        self._runtime_api_key: str | None = None
        self._lock = threading.RLock()
        self._warn_if_require_real_provider_is_deprecated()

    def get_status(self) -> ProviderStatus:
        _, configuration_source = self._resolve_api_key()
        configured = configuration_source is not ProviderConfigurationSource.MISSING
        return ProviderStatus(
            providerId=self.provider_id,
            modelId=self.model_id,
            configured=configured,
            configurationSource=configuration_source,
            canAnalyze=configured,
            canConfigureFromUi=configuration_source is ProviderConfigurationSource.MISSING,
        )

    def configure_runtime_key(self, api_key: str) -> ProviderStatus:
        normalized_key = api_key.strip()
        if not normalized_key:
            raise ValueError("apiKey 不能为空。")
        with self._lock:
            startup_key = self._read_startup_api_key()
            if startup_key is not None or self._runtime_api_key is not None:
                raise RuntimeError("provider 配置已锁定。")
            self._runtime_api_key = normalized_key
        log_event(
            logger,
            logging.INFO,
            "provider_runtime_key_configured",
            providerId=self.provider_id,
            modelId=self.model_id,
            configurationSource=ProviderConfigurationSource.RUNTIME_MEMORY.value,
        )
        return self.get_status()

    def reset_runtime_key(self) -> ProviderStatus:
        with self._lock:
            if self._read_startup_api_key() is not None:
                raise RuntimeError("provider 配置由启动环境变量提供，不能重置。")
            self._runtime_api_key = None
        if os.getenv(_ALLOW_E2E_PROVIDER_RESET_ENV) == "1":
            log_event(
                logger,
                logging.INFO,
                "provider_runtime_key_cleared",
                providerId=self.provider_id,
                modelId=self.model_id,
                configurationSource=ProviderConfigurationSource.MISSING.value,
            )
        return self.get_status()

    def require_configured_adapter(self) -> ProviderExecutionPort:
        api_key, configuration_source = self._resolve_api_key()
        if api_key is None:
            raise RuntimeError(f"{_DEEPSEEK_API_KEY_ENV} 未配置，当前不可执行分析。")
        provider_mode = "deepseek_real"
        if os.getenv(_E2E_PROVIDER_MODE_ENV) == _DETERMINISTIC_PROVIDER_MODE:
            provider_mode = _DETERMINISTIC_PROVIDER_MODE
        log_event(
            logger,
            logging.INFO,
            "provider_adapter_configured",
            providerMode=provider_mode,
            providerId=self.provider_id,
            modelId=self.model_id,
            configurationSource=configuration_source.value,
        )
        return build_configured_provider_adapter(api_key=api_key)

    def execute(self, request) -> object:
        return self.require_configured_adapter().execute(request)

    def _resolve_api_key(self) -> tuple[str | None, ProviderConfigurationSource]:
        startup_key = self._read_startup_api_key()
        if startup_key is not None:
            return startup_key, ProviderConfigurationSource.STARTUP_ENV
        with self._lock:
            if self._runtime_api_key is not None:
                return self._runtime_api_key, ProviderConfigurationSource.RUNTIME_MEMORY
        return None, ProviderConfigurationSource.MISSING

    def _read_startup_api_key(self) -> str | None:
        raw_value = os.getenv(_DEEPSEEK_API_KEY_ENV)
        if raw_value is None:
            return None
        normalized = raw_value.strip()
        return normalized or None

    def _warn_if_require_real_provider_is_deprecated(self) -> None:
        if os.getenv(_REQUIRE_REAL_PROVIDER_ENV) != "1":
            return
        log_event(
            logger,
            logging.WARNING,
            "require_real_provider_deprecated",
            environmentVariable=_REQUIRE_REAL_PROVIDER_ENV,
            message="API 已忽略 NOVEL_EVAL_REQUIRE_REAL_PROVIDER；缺少 key 时允许只读启动。",
        )


@lru_cache(maxsize=1)
def get_task_repository() -> SQLiteTaskRepository:
    db_path = resolve_db_path(os.getenv("NOVEL_EVAL_DB_PATH"))
    return SQLiteTaskRepository(db_path=db_path)


@lru_cache(maxsize=1)
def get_provider_runtime_state() -> ProviderRuntimeState:
    return ProviderRuntimeState()


def resolve_prompts_root(raw_path: str | None = None) -> Path:
    if raw_path is None or not raw_path.strip():
        return REPO_ROOT / "prompts"
    return Path(raw_path).expanduser().resolve()


def build_configured_provider_adapter(*, api_key: str) -> ProviderExecutionPort:
    provider_adapters_module = _get_provider_adapters_module()
    if os.getenv(_E2E_PROVIDER_MODE_ENV) == _DETERMINISTIC_PROVIDER_MODE:
        return provider_adapters_module.LocalDeterministicProviderAdapter(
            provider_id=_PROVIDER_ID,
            model_id=_MODEL_ID,
            structured_stage_outputs=True,
        )
    return provider_adapters_module.DeepSeekProviderAdapter(api_key=api_key)


def get_startup_provider_adapter() -> ProviderExecutionPort:
    api_key = os.getenv(_DEEPSEEK_API_KEY_ENV)
    if api_key is None or not api_key.strip():
        raise RuntimeError(f"worker 启动前必须设置 {_DEEPSEEK_API_KEY_ENV}。")
    return build_configured_provider_adapter(api_key=api_key.strip())


def get_provider_adapter() -> ProviderRuntimeExecutionPort:
    return get_provider_runtime_state()


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(
        task_repository=get_task_repository(),
        prompt_runtime=RuntimePromptRuntime(),
        provider_adapter=get_provider_adapter(),
    )


def recover_processing_tasks() -> None:
    service = get_evaluation_service()
    service.recover_incomplete_tasks()
