from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


class IdGenerator:
    def new_task_id(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class StaticIdGenerator(IdGenerator):
    value: str

    def new_task_id(self) -> str:
        return self.value


@dataclass(frozen=True)
class UuidTaskIdGenerator(IdGenerator):
    def new_task_id(self) -> str:
        return f"task_{uuid4().hex}"
