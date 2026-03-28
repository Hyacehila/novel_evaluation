from __future__ import annotations

from pydantic import field_validator

from packages.schemas.common.base import SchemaModel
from packages.schemas.common.validators import ensure_non_empty_text

_MAX_PROVIDER_API_KEY_LENGTH = 4096


class RuntimeProviderKeyRequest(SchemaModel):
    apiKey: str

    @field_validator("apiKey")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        normalized = ensure_non_empty_text(value, "apiKey")
        if len(normalized) > _MAX_PROVIDER_API_KEY_LENGTH:
            raise ValueError(f"apiKey 长度不能超过 {_MAX_PROVIDER_API_KEY_LENGTH} 个字符。")
        return normalized
