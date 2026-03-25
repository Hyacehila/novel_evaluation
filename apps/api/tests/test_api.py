from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import get_evaluation_service


def create_client() -> TestClient:
    get_evaluation_service.cache_clear()
    return TestClient(create_app())


def test_post_tasks_creates_task() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        json={
            "title": "测试稿件",
            "chapters": [{"title": "第一章", "content": "第一章内容"}],
            "outline": {"content": "大纲内容"},
            "sourceType": "direct_input",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["resultStatus"] == "not_available"


def test_post_tasks_rejects_invalid_payload() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        json={
            "title": "空输入",
            "chapters": [],
            "outline": None,
            "sourceType": "direct_input",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_get_task_returns_existing_task() -> None:
    client = create_client()
    created = client.post(
        "/api/tasks",
        json={
            "title": "测试稿件",
            "chapters": [{"title": "第一章", "content": "第一章内容"}],
            "outline": {"content": "大纲内容"},
            "sourceType": "direct_input",
        },
    ).json()["data"]

    response = client.get(f"/api/tasks/{created['taskId']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["taskId"] == created["taskId"]


def test_get_task_returns_404_for_missing_task() -> None:
    client = create_client()

    response = client.get("/api/tasks/missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "TASK_NOT_FOUND"


def test_get_result_returns_not_available_for_new_task() -> None:
    client = create_client()
    created = client.post(
        "/api/tasks",
        json={
            "title": "测试稿件",
            "chapters": [{"title": "第一章", "content": "第一章内容"}],
            "outline": {"content": "大纲内容"},
            "sourceType": "direct_input",
        },
    ).json()["data"]

    response = client.get(f"/api/tasks/{created['taskId']}/result")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["resultStatus"] == "not_available"
    assert payload["data"]["result"] is None


def test_get_dashboard_and_history_return_success() -> None:
    client = create_client()
    client.post(
        "/api/tasks",
        json={
            "title": "测试稿件",
            "chapters": [{"title": "第一章", "content": "第一章内容"}],
            "outline": {"content": "大纲内容"},
            "sourceType": "direct_input",
        },
    )

    dashboard = client.get("/api/dashboard")
    history = client.get("/api/history")

    assert dashboard.status_code == 200
    assert dashboard.json()["success"] is True
    assert len(dashboard.json()["data"]["recentTasks"]) == 1
    assert dashboard.json()["data"]["recentTasks"][0]["status"] == "queued"
    assert history.status_code == 200
    assert history.json()["success"] is True
    assert len(history.json()["data"]["items"]) == 1
    assert history.json()["data"]["items"][0]["resultStatus"] == "not_available"
    assert history.json()["meta"]["limit"] == 20
