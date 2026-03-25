from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


class Clock:
    def now(self) -> datetime:
        raise NotImplementedError


@dataclass(frozen=True)
class FixedClock(Clock):
    current: datetime

    def now(self) -> datetime:
        return self.current


@dataclass(frozen=True)
class UtcClock(Clock):
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
