from __future__ import annotations

from functools import lru_cache

from packages.application.services.evaluation_service import EvaluationService
from packages.runtime import service_factory as runtime_service_factory


PRIMARY_PROMPT_RUNTIME_SCOPES = runtime_service_factory.PRIMARY_PROMPT_RUNTIME_SCOPES
ApiPromptRuntime = runtime_service_factory.RuntimePromptRuntime
get_task_repository = runtime_service_factory.get_task_repository


def build_configured_provider_adapter(*, api_key: str):
    return runtime_service_factory.build_configured_provider_adapter(api_key=api_key)


class ApiProviderRuntimeState(runtime_service_factory.ProviderRuntimeState):
    def require_configured_adapter(self):
        api_key, configuration_source = self._resolve_api_key()
        if api_key is None:
            raise RuntimeError("NOVEL_EVAL_DEEPSEEK_API_KEY 未配置，当前不可执行分析。")
        runtime_service_factory.log_event(
            runtime_service_factory.logger,
            runtime_service_factory.logging.INFO,
            "provider_adapter_configured",
            providerMode=(
                "deterministic"
                if runtime_service_factory.os.getenv(runtime_service_factory._E2E_PROVIDER_MODE_ENV)
                == runtime_service_factory._DETERMINISTIC_PROVIDER_MODE
                else "deepseek_real"
            ),
            providerId=self.provider_id,
            modelId=self.model_id,
            configurationSource=configuration_source.value,
        )
        return build_configured_provider_adapter(api_key=api_key)


@lru_cache(maxsize=1)
def get_provider_runtime_state() -> ApiProviderRuntimeState:
    return ApiProviderRuntimeState()


def get_provider_adapter():
    return get_provider_runtime_state()


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(
        task_repository=get_task_repository(),
        prompt_runtime=ApiPromptRuntime(),
        provider_adapter=get_provider_adapter(),
    )


def recover_processing_tasks() -> None:
    get_evaluation_service().recover_incomplete_tasks()


__all__ = [
    "PRIMARY_PROMPT_RUNTIME_SCOPES",
    "ApiPromptRuntime",
    "ApiProviderRuntimeState",
    "build_configured_provider_adapter",
    "get_evaluation_service",
    "get_provider_adapter",
    "get_provider_runtime_state",
    "get_task_repository",
    "recover_processing_tasks",
]
