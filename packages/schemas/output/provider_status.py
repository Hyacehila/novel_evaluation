from __future__ import annotations

from enum import StrEnum

from pydantic import field_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.validators import ensure_non_empty_text


class ProviderConfigurationSource(StrEnum):
    MISSING = "missing"
    STARTUP_ENV = "startup_env"
    RUNTIME_MEMORY = "runtime_memory"


class ProviderStatus(SchemaModel):
    providerId: str
    modelId: str
    configured: bool
    configurationSource: ProviderConfigurationSource
    canAnalyze: bool
    canConfigureFromUi: bool

    @field_validator("providerId", "modelId")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        return ensure_non_empty_text(value, "provider_status.identifier")
