from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class SchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=False,
        use_enum_values=False,
    )


class MetaData(SchemaModel):
    nextCursor: str | None = None
    limit: int | None = None
    extra: dict[str, Any] | None = None
