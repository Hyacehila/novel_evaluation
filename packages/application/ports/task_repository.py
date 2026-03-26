from __future__ import annotations

from dataclasses import dataclass, field

from packages.schemas.common.enums import TaskStatus
from packages.schemas.output.result import EvaluationResultResource
from packages.schemas.output.task import EvaluationTask, EvaluationTaskSummary



def _sort_tasks(tasks: list[EvaluationTask]) -> list[EvaluationTask]:
    return sorted(tasks, key=lambda task: (task.createdAt, task.taskId), reverse=True)


class TaskRepository:
    def create_task(self, task: EvaluationTask) -> EvaluationTask:
        raise NotImplementedError

    def update_task(self, task: EvaluationTask) -> EvaluationTask:
        raise NotImplementedError

    def get_task(self, task_id: str) -> EvaluationTask | None:
        raise NotImplementedError

    def save_result(self, task_id: str, result: EvaluationResultResource) -> EvaluationResultResource:
        raise NotImplementedError

    def get_result(self, task_id: str) -> EvaluationResultResource | None:
        raise NotImplementedError

    def list_tasks(self) -> list[EvaluationTask]:
        raise NotImplementedError

    def list_task_ids_by_status(self, status: TaskStatus) -> list[str]:
        raise NotImplementedError


@dataclass(frozen=True)
class InMemoryTaskRepository(TaskRepository):
    _tasks: dict[str, EvaluationTask] = field(default_factory=dict)
    _results: dict[str, EvaluationResultResource] = field(default_factory=dict)

    def create_task(self, task: EvaluationTask) -> EvaluationTask:
        if task.taskId in self._tasks:
            raise ValueError("任务已存在。")
        self._tasks[task.taskId] = task
        return task

    def update_task(self, task: EvaluationTask) -> EvaluationTask:
        if task.taskId not in self._tasks:
            raise LookupError("任务不存在。")
        self._tasks[task.taskId] = task
        return task

    def get_task(self, task_id: str) -> EvaluationTask | None:
        return self._tasks.get(task_id)

    def save_result(self, task_id: str, result: EvaluationResultResource) -> EvaluationResultResource:
        if task_id not in self._tasks:
            raise LookupError("任务不存在。")
        self._results[task_id] = result
        return result

    def get_result(self, task_id: str) -> EvaluationResultResource | None:
        return self._results.get(task_id)

    def list_tasks(self) -> list[EvaluationTask]:
        return _sort_tasks(list(self._tasks.values()))

    def list_task_ids_by_status(self, status: TaskStatus) -> list[str]:
        return [task.taskId for task in self.list_tasks() if task.status is status]

    def list_task_summaries(self) -> list[EvaluationTaskSummary]:
        return [
            EvaluationTaskSummary(
                taskId=task.taskId,
                title=task.title,
                inputSummary=task.inputSummary,
                inputComposition=task.inputComposition,
                status=task.status,
                resultStatus=task.resultStatus,
                createdAt=task.createdAt,
            )
            for task in self.list_tasks()
        ]
