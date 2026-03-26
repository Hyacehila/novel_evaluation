from __future__ import annotations

import sqlite3
from pathlib import Path

from packages.application.ports.task_repository import TaskRepository
from packages.schemas.common.enums import TaskStatus
from packages.schemas.output.result import EvaluationResultResource
from packages.schemas.output.task import EvaluationTask


API_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = API_ROOT / "var" / "novel-evaluation.sqlite3"


class SQLiteTaskRepository(TaskRepository):
    def __init__(self, *, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create_task(self, task: EvaluationTask) -> EvaluationTask:
        payload = task.model_dump_json(exclude={"resultAvailable"})
        with self._connect() as connection:
            try:
                connection.execute(
                    "INSERT INTO tasks (task_id, created_at, payload) VALUES (?, ?, ?)",
                    (task.taskId, task.createdAt.isoformat(), payload),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("任务已存在。") from exc
        return task

    def update_task(self, task: EvaluationTask) -> EvaluationTask:
        payload = task.model_dump_json(exclude={"resultAvailable"})
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE tasks SET created_at = ?, payload = ? WHERE task_id = ?",
                (task.createdAt.isoformat(), payload, task.taskId),
            )
            if cursor.rowcount == 0:
                raise LookupError("任务不存在。")
        return task

    def get_task(self, task_id: str) -> EvaluationTask | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return EvaluationTask.model_validate_json(row[0])

    def save_result(self, task_id: str, result: EvaluationResultResource) -> EvaluationResultResource:
        if self.get_task(task_id) is None:
            raise LookupError("任务不存在。")
        payload = result.model_dump_json()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO results (task_id, payload) VALUES (?, ?) "
                "ON CONFLICT(task_id) DO UPDATE SET payload = excluded.payload",
                (task_id, payload),
            )
        return result

    def get_result(self, task_id: str) -> EvaluationResultResource | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM results WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return EvaluationResultResource.model_validate_json(row[0])

    def list_tasks(self) -> list[EvaluationTask]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM tasks ORDER BY created_at DESC, task_id DESC"
            ).fetchall()
        return [EvaluationTask.model_validate_json(row[0]) for row in rows]

    def list_task_ids_by_status(self, status: TaskStatus) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT task_id FROM tasks WHERE json_extract(payload, '$.status') = ? ORDER BY created_at DESC, task_id DESC",
                (status.value,),
            ).fetchall()
        return [row[0] for row in rows]

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                "task_id TEXT PRIMARY KEY, "
                "created_at TEXT NOT NULL, "
                "payload TEXT NOT NULL"
                ")"
            )
            connection.execute(
                "CREATE TABLE IF NOT EXISTS results ("
                "task_id TEXT PRIMARY KEY, "
                "payload TEXT NOT NULL, "
                "FOREIGN KEY(task_id) REFERENCES tasks(task_id) ON DELETE CASCADE"
                ")"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_created_at_task_id ON tasks(created_at DESC, task_id DESC)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection



def resolve_db_path(raw_path: str | None) -> Path:
    if raw_path is None or not raw_path.strip():
        return DEFAULT_DB_PATH
    return Path(raw_path).expanduser().resolve()


