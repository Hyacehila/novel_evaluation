from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import get_evaluation_service, get_task_repository
from packages.application.services.evaluation_service import EvaluationService
from packages.application.support.clock import FixedClock
from packages.application.support.id_generator import StaticIdGenerator
from packages.schemas.common.enums import ResultStatus, SubmissionSourceType, TaskStatus
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline
from packages.schemas.output.error import ErrorCode



def build_request() -> JointSubmissionRequest:
    return JointSubmissionRequest(
        title="持久化测试稿件",
        chapters=[ManuscriptChapter(title="第一章", content="第一章内容")],
        outline=ManuscriptOutline(content="大纲内容"),
        sourceType=SubmissionSourceType.DIRECT_INPUT,
    )



def create_client(*, db_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("NOVEL_EVAL_DB_PATH", str(db_path))
    get_evaluation_service.cache_clear()
    get_task_repository.cache_clear()
    return TestClient(create_app())



def test_sqlite_repository_persists_completed_result_across_instances(tmp_path: Path) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "state.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_persistence_001"),
        clock=FixedClock(datetime(2026, 3, 26, tzinfo=timezone.utc)),
    )

    task = service.create_task(build_request())
    service.start_task(task.taskId)
    service.complete_task_with_result(
        task.taskId,
        signing_probability=81,
        commercial_value=79,
        writing_quality=77,
        innovation_score=75,
    )

    reopened_repository = SQLiteTaskRepository(db_path=db_path)
    persisted_task = reopened_repository.get_task(task.taskId)
    persisted_result = reopened_repository.get_result(task.taskId)

    assert persisted_task is not None
    assert persisted_task.status is TaskStatus.COMPLETED
    assert persisted_task.resultStatus is ResultStatus.AVAILABLE
    assert persisted_result is not None
    assert persisted_result.resultStatus is ResultStatus.AVAILABLE
    assert persisted_result.result is not None
    assert persisted_result.result.signingProbability == 81



def test_api_restart_keeps_history_and_result_readable(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "runtime.sqlite3"

    with create_client(db_path=db_path, monkeypatch=monkeypatch) as client:
        created = client.post(
            "/api/tasks",
            json={
                "title": "重启后仍可读取",
                "chapters": [{"title": "第一章", "content": "第一章内容"}],
                "outline": {"content": "大纲内容"},
                "sourceType": "direct_input",
            },
        ).json()["data"]
        task_id = created["taskId"]

        task_payload = client.get(f"/api/tasks/{task_id}").json()["data"]
        result_payload = client.get(f"/api/tasks/{task_id}/result").json()["data"]
        history_payload = client.get("/api/history").json()["data"]

        assert created["status"] == "queued"
        assert created["resultStatus"] == "not_available"
        assert task_payload["status"] == "completed"
        assert task_payload["resultStatus"] == "available"
        assert result_payload["resultStatus"] == "available"
        assert result_payload["result"] is not None
        assert history_payload["items"][0]["taskId"] == task_id

    with create_client(db_path=db_path, monkeypatch=monkeypatch) as restarted_client:
        restarted_task = restarted_client.get(f"/api/tasks/{task_id}")
        restarted_result = restarted_client.get(f"/api/tasks/{task_id}/result")
        restarted_history = restarted_client.get("/api/history")

        assert restarted_task.status_code == 200
        assert restarted_task.json()["data"]["status"] == "completed"
        assert restarted_task.json()["data"]["resultStatus"] == "available"
        assert restarted_result.status_code == 200
        assert restarted_result.json()["data"]["resultStatus"] == "available"
        assert restarted_result.json()["data"]["result"] is not None
        assert restarted_history.status_code == 200
        assert restarted_history.json()["data"]["items"][0]["taskId"] == task_id



def test_api_restart_marks_stale_processing_task_failed(tmp_path: Path, monkeypatch) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "recovery.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_recovery_001"),
        clock=FixedClock(datetime(2026, 3, 26, tzinfo=timezone.utc)),
    )

    task = service.create_task(build_request())
    processing_task = service.start_task(task.taskId)

    assert processing_task.status is TaskStatus.PROCESSING

    with create_client(db_path=db_path, monkeypatch=monkeypatch) as client:
        task_response = client.get(f"/api/tasks/{task.taskId}")
        result_response = client.get(f"/api/tasks/{task.taskId}/result")

        assert task_response.status_code == 200
        assert task_response.json()["data"]["status"] == "failed"
        assert task_response.json()["data"]["resultStatus"] == "not_available"
        assert task_response.json()["data"]["errorCode"] == ErrorCode.INTERNAL_ERROR.value
        assert "重启" in task_response.json()["data"]["errorMessage"]
        assert result_response.status_code == 200
        assert result_response.json()["data"]["resultStatus"] == "not_available"
        assert result_response.json()["data"]["result"] is None



def test_history_orders_latest_tasks_first_across_restart(tmp_path: Path, monkeypatch) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "history.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    early_service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_history_early"),
        clock=FixedClock(datetime(2026, 3, 26, 0, 0, tzinfo=timezone.utc)),
    )
    late_service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_history_late"),
        clock=FixedClock(datetime(2026, 3, 26, 0, 1, tzinfo=timezone.utc)),
    )

    early_service.create_task(build_request())
    late_service.create_task(build_request())

    with create_client(db_path=db_path, monkeypatch=monkeypatch) as client:
        history_response = client.get("/api/history")
        items = history_response.json()["data"]["items"]

        assert history_response.status_code == 200
        assert items[0]["taskId"] == "task_history_late"
        assert items[1]["taskId"] == "task_history_early"



def test_default_db_path_is_stable_absolute_location() -> None:
    from api.sqlite_repository import API_ROOT, DEFAULT_DB_PATH, resolve_db_path

    resolved = resolve_db_path(None)

    assert resolved == DEFAULT_DB_PATH
    assert resolved.is_absolute()
    assert resolved == API_ROOT / "var" / "novel-evaluation.sqlite3"
