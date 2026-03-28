from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from api import dependencies as api_dependencies
from api.app import create_app
from api.dependencies import get_evaluation_service, get_provider_runtime_state, get_task_repository
from packages.application.services.evaluation_service import EvaluationService
from packages.application.support.clock import FixedClock
from packages.application.support.id_generator import StaticIdGenerator
from packages.schemas.common.enums import ResultStatus, SubmissionSourceType, TaskStatus
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline
from packages.schemas.output.error import ErrorCode



def configure_fake_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        api_dependencies,
        "build_configured_provider_adapter",
        lambda *, api_key: api_dependencies._get_provider_adapters_module().LocalDeterministicProviderAdapter(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            structured_stage_outputs=True,
        ),
    )



def build_request() -> JointSubmissionRequest:
    return JointSubmissionRequest(
        title="持久化测试稿件",
        chapters=[ManuscriptChapter(title="第一章", content="第一章内容")],
        outline=ManuscriptOutline(content="大纲内容"),
        sourceType=SubmissionSourceType.DIRECT_INPUT,
    )



def create_client(*, db_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("NOVEL_EVAL_DB_PATH", str(db_path))
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "test-key")
    configure_fake_provider(monkeypatch)
    get_evaluation_service.cache_clear()
    get_task_repository.cache_clear()
    get_provider_runtime_state.cache_clear()
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
    assert persisted_result.result.overall.score == 81
    assert len(persisted_result.result.axes) == 8



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



def test_sqlite_repository_returns_not_available_for_legacy_persisted_result_json(tmp_path: Path) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "legacy.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_legacy_001"),
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

    legacy_payload = {
        "taskId": task.taskId,
        "resultStatus": "available",
        "resultTime": "2026-03-26T00:00:00Z",
        "result": {
            "taskId": task.taskId,
            "schemaVersion": "1.0.0",
            "promptVersion": "prompt-v1",
            "rubricVersion": "rubric-v1",
            "providerId": "provider-local",
            "modelId": "model-local",
            "resultTime": "2026-03-26T00:00:00Z",
            "signingProbability": 80,
            "commercialValue": 78,
            "writingQuality": 76,
            "innovationScore": 74,
            "strengths": ["人物动机清晰"],
            "weaknesses": ["开篇冲突偏慢"],
            "platforms": [
                {
                    "name": "女频平台 A",
                    "percentage": 82,
                    "reason": "题材匹配度较高",
                }
            ],
            "marketFit": "具备一定市场接受度",
            "editorVerdict": "可继续观察",
            "detailedAnalysis": {
                "plot": "情节推进稳定",
                "character": "角色动机明确",
                "pacing": "节奏略慢",
                "worldBuilding": "设定表达完整",
            },
        },
    }
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE results SET payload = ? WHERE task_id = ?",
            (json.dumps(legacy_payload, ensure_ascii=False), task.taskId),
        )

    persisted_result = repository.get_result(task.taskId)

    assert persisted_result is not None
    assert persisted_result.resultStatus is ResultStatus.NOT_AVAILABLE
    assert persisted_result.result is None
    assert persisted_result.message == "历史结果结构已过期，无法按当前 8 轴契约展示，请重新提交新任务。"



def test_api_result_endpoint_returns_not_available_for_legacy_persisted_result_after_restart(tmp_path: Path, monkeypatch) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "legacy-api.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_legacy_api_001"),
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

    legacy_payload = {
        "taskId": task.taskId,
        "resultStatus": "available",
        "resultTime": "2026-03-26T00:00:00Z",
        "result": {
            "taskId": task.taskId,
            "schemaVersion": "1.0.0",
            "promptVersion": "prompt-v1",
            "rubricVersion": "rubric-v1",
            "providerId": "provider-local",
            "modelId": "model-local",
            "resultTime": "2026-03-26T00:00:00Z",
            "signingProbability": 80,
            "commercialValue": 78,
            "writingQuality": 76,
            "innovationScore": 74,
            "strengths": ["人物动机清晰"],
            "weaknesses": ["开篇冲突偏慢"],
            "platforms": [
                {
                    "name": "女频平台 A",
                    "percentage": 82,
                    "reason": "题材匹配度较高",
                }
            ],
            "marketFit": "具备一定市场接受度",
            "editorVerdict": "可继续观察",
            "detailedAnalysis": {
                "plot": "情节推进稳定",
                "character": "角色动机明确",
                "pacing": "节奏略慢",
                "worldBuilding": "设定表达完整",
            },
        },
    }
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE results SET payload = ? WHERE task_id = ?",
            (json.dumps(legacy_payload, ensure_ascii=False), task.taskId),
        )

    with create_client(db_path=db_path, monkeypatch=monkeypatch) as client:
        repository_after_restart = api_dependencies.get_task_repository()
        assert repository_after_restart.get_result(task.taskId) is not None
        result_response = client.get(f"/api/tasks/{task.taskId}/result")

    assert result_response.status_code == 200
    payload = result_response.json()
    assert payload["data"]["resultStatus"] == "not_available"
    assert payload["data"]["result"] is None
    assert payload["data"]["message"] == "历史结果结构已过期，无法按当前 8 轴契约展示，请重新提交新任务。"



def test_sqlite_repository_returns_not_available_when_result_payload_is_corrupted(tmp_path: Path) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "legacy-corrupted.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_legacy_bad_001"),
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

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE results SET payload = ? WHERE task_id = ?",
            ("{bad-json", task.taskId),
        )

    persisted_result = repository.get_result(task.taskId)

    assert persisted_result is not None
    assert persisted_result.resultStatus is ResultStatus.NOT_AVAILABLE
    assert persisted_result.result is None
    assert persisted_result.message == "结果数据已损坏，当前不可展示，请重新提交新任务。"



def test_sqlite_repository_returns_not_available_when_legacy_result_payload_missing_nested_task_id(tmp_path: Path) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "legacy-missing-nested-task-id.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_legacy_missing_nested_id_001"),
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

    legacy_payload = {
        "taskId": task.taskId,
        "resultStatus": "available",
        "resultTime": "2026-03-26T00:00:00Z",
        "result": {
            "schemaVersion": "1.0.0",
            "promptVersion": "prompt-v1",
            "rubricVersion": "rubric-v1",
            "providerId": "provider-local",
            "modelId": "model-local",
            "resultTime": "2026-03-26T00:00:00Z",
            "signingProbability": 80,
            "commercialValue": 78,
            "writingQuality": 76,
            "innovationScore": 74,
            "platforms": [{"name": "女频平台 A"}],
            "marketFit": "具备一定市场接受度",
            "editorVerdict": "可继续观察",
            "detailedAnalysis": {
                "plot": "情节推进稳定",
                "character": "角色动机明确",
                "pacing": "节奏略慢",
                "worldBuilding": "设定表达完整",
            },
        },
    }
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE results SET payload = ? WHERE task_id = ?",
            (json.dumps(legacy_payload, ensure_ascii=False), task.taskId),
        )

    persisted_result = repository.get_result(task.taskId)

    assert persisted_result is not None
    assert persisted_result.resultStatus is ResultStatus.NOT_AVAILABLE
    assert persisted_result.result is None
    assert persisted_result.message == "历史结果结构已过期，无法按当前 8 轴契约展示，请重新提交新任务。"



def test_sqlite_repository_returns_not_available_when_legacy_result_payload_uses_bool_score(tmp_path: Path) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "legacy-bool-score.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_legacy_bool_score_001"),
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

    legacy_payload = {
        "taskId": task.taskId,
        "resultStatus": "available",
        "resultTime": "2026-03-26T00:00:00Z",
        "result": {
            "taskId": task.taskId,
            "schemaVersion": "1.0.0",
            "promptVersion": "prompt-v1",
            "rubricVersion": "rubric-v1",
            "providerId": "provider-local",
            "modelId": "model-local",
            "resultTime": "2026-03-26T00:00:00Z",
            "signingProbability": True,
            "commercialValue": 78,
            "writingQuality": 76,
            "innovationScore": 74,
            "platforms": [{"name": "女频平台 A"}],
            "marketFit": "具备一定市场接受度",
            "editorVerdict": "可继续观察",
            "detailedAnalysis": {
                "plot": "情节推进稳定",
                "character": "角色动机明确",
                "pacing": "节奏略慢",
                "worldBuilding": "设定表达完整",
            },
        },
    }
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE results SET payload = ? WHERE task_id = ?",
            (json.dumps(legacy_payload, ensure_ascii=False), task.taskId),
        )

    persisted_result = repository.get_result(task.taskId)

    assert persisted_result is not None
    assert persisted_result.resultStatus is ResultStatus.NOT_AVAILABLE
    assert persisted_result.result is None
    assert persisted_result.message == "历史结果结构已过期，无法按当前 8 轴契约展示，请重新提交新任务。"



def test_sqlite_repository_returns_not_available_when_current_result_payload_is_damaged(tmp_path: Path) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "current-result-damaged.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_current_result_damaged_001"),
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

    persisted_result = repository.get_result(task.taskId)
    assert persisted_result is not None
    damaged_payload = persisted_result.model_dump(mode="json")
    damaged_payload["result"]["axes"] = "bad-axes"

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE results SET payload = ? WHERE task_id = ?",
            (json.dumps(damaged_payload, ensure_ascii=False), task.taskId),
        )

    reloaded_result = repository.get_result(task.taskId)

    assert reloaded_result is not None
    assert reloaded_result.resultStatus is ResultStatus.NOT_AVAILABLE
    assert reloaded_result.result is None
    assert reloaded_result.message == "结果数据已损坏，当前不可展示，请重新提交新任务。"



def test_api_dashboard_skips_corrupted_result_payload_after_restart(tmp_path: Path, monkeypatch) -> None:
    from api.sqlite_repository import SQLiteTaskRepository

    db_path = tmp_path / "legacy-dashboard-corrupted.sqlite3"
    repository = SQLiteTaskRepository(db_path=db_path)
    service = EvaluationService(
        task_repository=repository,
        id_generator=StaticIdGenerator("task_legacy_dash_001"),
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

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "UPDATE results SET payload = ? WHERE task_id = ?",
            ("{bad-json", task.taskId),
        )

    with create_client(db_path=db_path, monkeypatch=monkeypatch) as client:
        task_response = client.get(f"/api/tasks/{task.taskId}")
        history_response = client.get("/api/history")
        result_response = client.get(f"/api/tasks/{task.taskId}/result")
        dashboard_response = client.get("/api/dashboard")

    assert task_response.status_code == 200
    task_payload = task_response.json()["data"]
    assert task_payload["status"] == "completed"
    assert task_payload["resultStatus"] == "not_available"
    assert result_response.status_code == 200
    result_payload = result_response.json()["data"]
    assert result_payload["resultStatus"] == "not_available"
    assert result_payload["result"] is None
    assert result_payload["message"] == "结果数据已损坏，当前不可展示，请重新提交新任务。"
    assert history_response.status_code == 200
    assert history_response.json()["data"]["items"][0]["resultStatus"] == "not_available"
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["data"]["recentTasks"][0]["resultStatus"] == "not_available"
    assert dashboard_response.json()["data"]["recentResults"] == []



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
