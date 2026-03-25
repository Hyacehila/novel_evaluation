from __future__ import annotations

from functools import lru_cache

from packages.application.ports.task_repository import InMemoryTaskRepository
from packages.application.services.evaluation_service import EvaluationService


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService(task_repository=InMemoryTaskRepository())
