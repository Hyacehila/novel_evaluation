from __future__ import annotations

from typing import Generic, Literal, TypeVar

from packages.schemas.common.base import MetaData, SchemaModel
from packages.schemas.output.error import ErrorObject


DataType = TypeVar("DataType")


class SuccessEnvelope(SchemaModel, Generic[DataType]):
    success: Literal[True] = True
    data: DataType
    error: None = None
    meta: MetaData | None = None


class ErrorEnvelope(SchemaModel):
    success: Literal[False] = False
    data: None = None
    error: ErrorObject
    meta: MetaData | None = None
