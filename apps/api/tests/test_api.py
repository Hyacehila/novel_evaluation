from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

import json
import pytest
from docx import Document
from fastapi.testclient import TestClient

from api import dependencies as api_dependencies
from api.app import create_app
from api.dependencies import (
    PRIMARY_PROMPT_RUNTIME_SCOPES,
    ApiPromptRuntime,
    get_evaluation_service,
    get_provider_runtime_state,
    get_task_repository,
)
from packages.schemas.common.enums import EvaluationMode, InputComposition, ResultStatus, TaskStatus
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.task import EvaluationTask


@pytest.fixture(autouse=True)
def configure_fake_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(
        api_dependencies,
        "build_configured_provider_adapter",
        lambda *, api_key: api_dependencies._get_provider_adapters_module().LocalDeterministicProviderAdapter(
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
            structured_stage_outputs=True,
        ),
    )



def create_client(*, client: tuple[str, int] = ("testclient", 50000)) -> TestClient:
    get_evaluation_service.cache_clear()
    get_task_repository.cache_clear()
    get_provider_runtime_state.cache_clear()
    return TestClient(create_app(), client=client)


def make_docx_bytes(paragraphs: list[str]) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def seed_task(
    *,
    task_id: str,
    title: str,
    created_at: datetime,
    status: TaskStatus = TaskStatus.COMPLETED,
    result_status: ResultStatus = ResultStatus.AVAILABLE,
) -> EvaluationTask:
    repository = get_task_repository()
    started_at = created_at if status in {TaskStatus.PROCESSING, TaskStatus.COMPLETED, TaskStatus.FAILED} else None
    completed_at = created_at if status in {TaskStatus.COMPLETED, TaskStatus.FAILED} else None
    error_code = ErrorCode.INTERNAL_ERROR if status is TaskStatus.FAILED else None
    error_message = "服务暂时不可用" if status is TaskStatus.FAILED else None
    task = EvaluationTask(
        taskId=task_id,
        title=title,
        inputSummary="已提交 1 章正文和 1 份大纲",
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        hasChapters=True,
        hasOutline=True,
        evaluationMode=EvaluationMode.FULL,
        status=status,
        resultStatus=result_status,
        errorCode=error_code,
        errorMessage=error_message,
        createdAt=created_at,
        startedAt=started_at,
        completedAt=completed_at,
        updatedAt=created_at,
    )
    return repository.create_task(task)


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
    assert payload["data"]["schemaVersion"] == "1.0.0"
    assert payload["data"]["promptVersion"] == "v1"
    assert payload["data"]["rubricVersion"] == "rubric-v1"
    assert payload["data"]["providerId"] == "provider-deepseek"
    assert payload["data"]["modelId"] == "deepseek-chat"


def test_post_tasks_accepts_multipart_chapters_file_without_auto_split() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        data={"title": "上传正文", "sourceType": "file_upload"},
        files={"chaptersFile": ("chapter.txt", "第一章\n内容\n\n第二章\n内容", "text/plain")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["resultStatus"] == "not_available"
    assert payload["data"]["inputComposition"] == "chapters_only"
    assert payload["data"]["evaluationMode"] == "degraded"
    assert payload["data"]["inputSummary"] == "仅提交 1 章正文"


def test_post_tasks_accepts_multipart_outline_file() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        data={"title": "上传大纲", "sourceType": "file_upload"},
        files={"outlineFile": ("outline.md", "# 大纲\n主要剧情", "text/markdown")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["inputComposition"] == "outline_only"
    assert payload["data"]["evaluationMode"] == "degraded"


def test_post_tasks_accepts_multipart_docx_and_outline_file() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        data={"title": "组合上传", "sourceType": "file_upload"},
        files={
            "chaptersFile": (
                "chapter.docx",
                make_docx_bytes(["第一段正文", "第二段正文"]),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            "outlineFile": ("outline.md", "# 大纲\n主要剧情", "text/markdown"),
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["inputComposition"] == "chapters_outline"
    assert payload["data"]["evaluationMode"] == "full"


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


def test_post_tasks_rejects_empty_multipart_submission() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        files=[("title", (None, "空上传")), ("sourceType", (None, "file_upload"))],
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "EMPTY_SUBMISSION"


def test_post_tasks_rejects_invalid_source_type_in_multipart() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        data={"title": "非法来源", "sourceType": "invalid"},
        files={"chaptersFile": ("chapter.txt", "正文内容", "text/plain")},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_SOURCE_TYPE"


def test_post_tasks_rejects_unsupported_upload_format() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        data={"title": "非法格式", "sourceType": "file_upload"},
        files={"chaptersFile": ("chapter.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UNSUPPORTED_UPLOAD_FORMAT"
    assert get_task_repository().list_tasks() == []


def test_post_tasks_rejects_upload_too_large(monkeypatch) -> None:
    client = create_client()
    monkeypatch.setenv("NOVEL_EVAL_UPLOAD_MAX_BYTES", "4")

    response = client.post(
        "/api/tasks",
        data={"title": "超大文件", "sourceType": "file_upload"},
        files={"chaptersFile": ("chapter.txt", b"12345", "text/plain")},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UPLOAD_TOO_LARGE"
    assert get_task_repository().list_tasks() == []


def test_post_tasks_rejects_invalid_docx_upload() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        data={"title": "损坏文档", "sourceType": "file_upload"},
        files={
            "chaptersFile": (
                "broken.docx",
                b"not-a-valid-docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UPLOAD_PARSE_FAILED"
    assert get_task_repository().list_tasks() == []


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
    assert payload["data"]["schemaVersion"] == "1.0.0"
    assert payload["data"]["promptVersion"] == "v1"
    assert payload["data"]["rubricVersion"] == "rubric-v1"
    assert payload["data"]["providerId"] == "provider-deepseek"
    assert payload["data"]["modelId"] == "deepseek-chat"


def test_get_task_returns_404_for_missing_task() -> None:
    client = create_client()

    response = client.get("/api/tasks/missing")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "TASK_NOT_FOUND"


def test_get_result_returns_available_after_in_process_execution() -> None:
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
    assert payload["data"]["resultStatus"] == "available"
    assert payload["data"]["result"] is not None
    assert len(payload["data"]["result"]["axes"]) == 8
    assert payload["data"]["result"]["overall"]["score"] == 70
    assert payload["data"]["result"]["overall"]["verdict"] == "建议继续观察并进入样章复核。"
    assert "signingProbability" not in payload["data"]["result"]


def test_get_provider_status_returns_startup_env_state() -> None:
    client = create_client()

    response = client.get("/api/provider-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] == {
        "providerId": "provider-deepseek",
        "modelId": "deepseek-chat",
        "configured": True,
        "configurationSource": "startup_env",
        "canAnalyze": True,
        "canConfigureFromUi": False,
    }



def test_post_tasks_masks_provider_failure_message_in_task_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "test-key")

    provider_adapters_module = api_dependencies._get_provider_adapters_module()

    class RawFailureProviderAdapter:
        provider_id = "provider-deepseek"
        model_id = "deepseek-chat"

        def execute(self, request):
            return provider_adapters_module.build_provider_failure(
                provider_id=self.provider_id,
                model_id=self.model_id,
                request_id=request.requestId,
                provider_request_id="req-secret-001",
                duration_ms=1,
                failure_type=provider_adapters_module.ProviderFailureType.PROVIDER_FAILURE,
                message="raw upstream api key sk-secret exposed in provider failure",
            )

    monkeypatch.setattr(
        api_dependencies,
        "build_configured_provider_adapter",
        lambda *, api_key: RawFailureProviderAdapter(),
    )
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

    task_response = client.get(f"/api/tasks/{created['taskId']}")

    assert task_response.status_code == 200
    payload = task_response.json()
    assert payload["data"]["status"] == "failed"
    assert payload["data"]["resultStatus"] == "not_available"
    assert payload["data"]["errorCode"] == ErrorCode.PROVIDER_FAILURE.value
    assert "deterministic adapter" not in payload["data"]["errorMessage"]
    assert "provider_failure" not in payload["data"]["errorMessage"]



def test_post_tasks_masks_screening_block_message_in_task_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "test-key")

    class RawSuccess:
        def __init__(self, raw_json):
            self.rawJson = raw_json
            self.rawText = "{}"

    class ScreeningBlockedProviderAdapter:
        provider_id = "provider-deepseek"
        model_id = "deepseek-chat"

        def execute(self, request):
            if request.stage.value != "input_screening":
                raise AssertionError(f"unexpected stage: {request.stage.value}")
            return RawSuccess(
                {
                    "inputComposition": "chapters_outline",
                    "evaluationMode": "degraded",
                    "chaptersSufficiency": "insufficient",
                    "outlineSufficiency": "sufficient",
                    "rateable": False,
                    "status": "unrateable",
                    "rejectionReasons": ["raw upstream provider reason sk-secret should not leak"],
                    "riskTags": ["insufficientMaterial"],
                    "confidence": 0.2,
                    "continueAllowed": False,
                }
            )

    monkeypatch.setattr(
        api_dependencies,
        "build_configured_provider_adapter",
        lambda *, api_key: ScreeningBlockedProviderAdapter(),
    )
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

    task_response = client.get(f"/api/tasks/{created['taskId']}")

    assert task_response.status_code == 200
    payload = task_response.json()
    assert payload["data"]["status"] == "completed"
    assert payload["data"]["resultStatus"] == "blocked"
    assert payload["data"]["errorCode"] == ErrorCode.INSUFFICIENT_CHAPTERS_INPUT.value
    assert payload["data"]["errorMessage"] == "正文内容不足，当前无法进入正式评分，请补充正文后重试。"
    assert "raw upstream" not in payload["data"]["errorMessage"]
    assert "sk-secret" not in payload["data"]["errorMessage"]

    result_response = client.get(f"/api/tasks/{created['taskId']}/result")
    assert result_response.status_code == 200
    assert result_response.json()["data"]["message"] == "结果未满足正式展示条件"



def test_post_tasks_masks_outline_screening_block_message_in_task_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "test-key")

    class RawSuccess:
        def __init__(self, raw_json):
            self.rawJson = raw_json
            self.rawText = "{}"

    class OutlineBlockedProviderAdapter:
        provider_id = "provider-deepseek"
        model_id = "deepseek-chat"

        def execute(self, request):
            if request.stage.value != "input_screening":
                raise AssertionError(f"unexpected stage: {request.stage.value}")
            return RawSuccess(
                {
                    "inputComposition": "outline_only",
                    "evaluationMode": "degraded",
                    "chaptersSufficiency": "missing",
                    "outlineSufficiency": "insufficient",
                    "rateable": False,
                    "status": "unrateable",
                    "rejectionReasons": ["outline upstream provider reason sk-secret should not leak"],
                    "riskTags": ["insufficientMaterial"],
                    "confidence": 0.2,
                    "continueAllowed": False,
                }
            )

    monkeypatch.setattr(
        api_dependencies,
        "build_configured_provider_adapter",
        lambda *, api_key: OutlineBlockedProviderAdapter(),
    )
    client = create_client()

    created = client.post(
        "/api/tasks",
        json={
            "title": "仅大纲阻断",
            "outline": {"content": "大纲内容"},
            "sourceType": "direct_input",
        },
    ).json()["data"]

    task_response = client.get(f"/api/tasks/{created['taskId']}")

    assert task_response.status_code == 200
    payload = task_response.json()
    assert payload["data"]["status"] == "completed"
    assert payload["data"]["resultStatus"] == "blocked"
    assert payload["data"]["errorCode"] == ErrorCode.INSUFFICIENT_OUTLINE_INPUT.value
    assert payload["data"]["errorMessage"] == "大纲内容不足，当前无法进入正式评分，请补充大纲后重试。"
    assert "upstream" not in payload["data"]["errorMessage"]
    assert "sk-secret" not in payload["data"]["errorMessage"]



def test_post_tasks_masks_joint_unrateable_screening_block_message_in_task_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "test-key")

    class RawSuccess:
        def __init__(self, raw_json):
            self.rawJson = raw_json
            self.rawText = "{}"

    class JointUnrateableProviderAdapter:
        provider_id = "provider-deepseek"
        model_id = "deepseek-chat"

        def execute(self, request):
            if request.stage.value != "input_screening":
                raise AssertionError(f"unexpected stage: {request.stage.value}")
            return RawSuccess(
                {
                    "inputComposition": "chapters_outline",
                    "evaluationMode": "degraded",
                    "chaptersSufficiency": "sufficient",
                    "outlineSufficiency": "sufficient",
                    "rateable": False,
                    "status": "unrateable",
                    "rejectionReasons": ["joint upstream provider reason sk-secret should not leak"],
                    "riskTags": [],
                    "confidence": 0.7,
                    "continueAllowed": False,
                }
            )

    monkeypatch.setattr(
        api_dependencies,
        "build_configured_provider_adapter",
        lambda *, api_key: JointUnrateableProviderAdapter(),
    )
    client = create_client()

    created = client.post(
        "/api/tasks",
        json={
            "title": "联合不可评阻断",
            "chapters": [{"title": "第一章", "content": "第一章内容"}],
            "outline": {"content": "大纲内容"},
            "sourceType": "direct_input",
        },
    ).json()["data"]

    task_response = client.get(f"/api/tasks/{created['taskId']}")

    assert task_response.status_code == 200
    payload = task_response.json()
    assert payload["data"]["status"] == "completed"
    assert payload["data"]["resultStatus"] == "blocked"
    assert payload["data"]["errorCode"] == ErrorCode.JOINT_INPUT_UNRATEABLE.value
    assert payload["data"]["errorMessage"] == "输入材料未满足正式评分条件，当前无法进入正式评分，请补充材料后重试。"
    assert "upstream" not in payload["data"]["errorMessage"]
    assert "sk-secret" not in payload["data"]["errorMessage"]


def test_get_provider_status_returns_missing_state_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    client = create_client()

    response = client.get("/api/provider-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] == {
        "providerId": "provider-deepseek",
        "modelId": "deepseek-chat",
        "configured": False,
        "configurationSource": "missing",
        "canAnalyze": False,
        "canConfigureFromUi": True,
    }


def test_runtime_key_configuration_enables_analysis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    client = create_client()

    configure_response = client.post("/api/provider-status/runtime-key", json={"apiKey": "runtime-key"})

    assert configure_response.status_code == 200
    status_response = client.get("/api/provider-status")
    assert status_response.status_code == 200
    assert status_response.json()["data"] == {
        "providerId": "provider-deepseek",
        "modelId": "deepseek-chat",
        "configured": True,
        "configurationSource": "runtime_memory",
        "canAnalyze": True,
        "canConfigureFromUi": False,
    }


def test_runtime_key_configuration_rejects_blank_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    client = create_client()

    response = client.post("/api/provider-status/runtime-key", json={"apiKey": "   "})

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_runtime_key_configuration_rejects_oversized_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    client = create_client()

    response = client.post("/api/provider-status/runtime-key", json={"apiKey": "k" * 4097})

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_runtime_key_configuration_is_locked_when_startup_key_exists() -> None:
    client = create_client()

    response = client.post("/api/provider-status/runtime-key", json={"apiKey": "other-key"})

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "PROVIDER_CONFIGURATION_LOCKED"


def test_runtime_key_configuration_rejects_non_local_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    client = create_client(client=("203.0.113.10", 50000))

    response = client.post("/api/provider-status/runtime-key", json={"apiKey": "runtime-key"})

    assert response.status_code == 403
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "FORBIDDEN"


def test_runtime_key_configuration_rejects_forwarded_local_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    client = create_client(client=("127.0.0.1", 50000))

    response = client.post(
        "/api/provider-status/runtime-key",
        json={"apiKey": "runtime-key"},
        headers={"x-forwarded-for": "203.0.113.10"},
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "FORBIDDEN"


def test_runtime_key_reset_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("NOVEL_EVAL_E2E_ALLOW_PROVIDER_RESET", raising=False)
    client = create_client()

    response = client.delete("/api/provider-status/runtime-key")

    assert response.status_code == 403
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "FORBIDDEN"


def test_runtime_key_reset_clears_runtime_configuration_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("NOVEL_EVAL_E2E_ALLOW_PROVIDER_RESET", "1")
    client = create_client()

    configure_response = client.post("/api/provider-status/runtime-key", json={"apiKey": "runtime-key"})
    assert configure_response.status_code == 200

    reset_response = client.delete("/api/provider-status/runtime-key")

    assert reset_response.status_code == 200
    assert reset_response.json()["data"] == {
        "providerId": "provider-deepseek",
        "modelId": "deepseek-chat",
        "configured": False,
        "configurationSource": "missing",
        "canAnalyze": False,
        "canConfigureFromUi": True,
    }


def test_runtime_key_reset_is_locked_when_startup_key_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_E2E_ALLOW_PROVIDER_RESET", "1")
    client = create_client()

    response = client.delete("/api/provider-status/runtime-key")

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "PROVIDER_CONFIGURATION_LOCKED"


def test_api_starts_without_provider_key_and_keeps_read_only_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_REQUIRE_REAL_PROVIDER", "1")
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    client = create_client()

    dashboard = client.get("/api/dashboard")
    history = client.get("/api/history")

    assert dashboard.status_code == 200
    assert dashboard.json()["success"] is True
    assert history.status_code == 200
    assert history.json()["success"] is True


def test_post_tasks_rejects_when_provider_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
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

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "PROVIDER_NOT_CONFIGURED"
    assert get_task_repository().list_tasks() == []


def test_post_tasks_allows_creation_after_runtime_key_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)
    client = create_client()
    configure_response = client.post("/api/provider-status/runtime-key", json={"apiKey": "runtime-key"})

    assert configure_response.status_code == 200

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
    assert payload["data"]["providerId"] == "provider-deepseek"
    assert payload["data"]["modelId"] == "deepseek-chat"


def test_post_tasks_keeps_degraded_input_semantics() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        json={
            "title": "只有大纲",
            "outline": {"content": "大纲内容"},
            "sourceType": "direct_input",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["resultStatus"] == "not_available"
    assert payload["data"]["evaluationMode"] == "degraded"
    assert payload["data"]["inputComposition"] == "outline_only"
    assert payload["data"]["schemaVersion"] == "1.0.0"
    assert payload["data"]["promptVersion"] == "v1"
    assert payload["data"]["rubricVersion"] == "rubric-v1"
    assert payload["data"]["providerId"] == "provider-deepseek"
    assert payload["data"]["modelId"] == "deepseek-chat"


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
    assert dashboard.json()["data"]["recentTasks"][0]["status"] == "completed"
    assert dashboard.json()["data"]["recentTasks"][0]["resultStatus"] == "available"
    assert len(dashboard.json()["data"]["recentResults"]) == 1
    assert dashboard.json()["data"]["recentResults"][0]["overallScore"] == 70
    assert dashboard.json()["data"]["recentResults"][0]["overallVerdict"] == "建议继续观察并进入样章复核。"
    assert "signingProbability" not in dashboard.json()["data"]["recentResults"][0]
    assert history.status_code == 200
    assert history.json()["success"] is True
    assert len(history.json()["data"]["items"]) == 1
    assert history.json()["data"]["items"][0]["resultStatus"] == "available"
    assert history.json()["meta"]["limit"] == 20


def test_get_history_filters_by_title_query() -> None:
    client = create_client()
    base_time = datetime(2026, 3, 26, 12, 0, tzinfo=timezone.utc)
    seed_task(task_id="task_a", title="星际远征", created_at=base_time)
    seed_task(task_id="task_b", title="都市日常", created_at=base_time.replace(minute=1))
    seed_task(task_id="task_c", title="星际余烬", created_at=base_time.replace(minute=2))

    response = client.get("/api/history", params={"q": "星际"})

    assert response.status_code == 200
    payload = response.json()
    assert [item["title"] for item in payload["data"]["items"]] == ["星际余烬", "星际远征"]


def test_get_history_filters_by_status() -> None:
    client = create_client()
    base_time = datetime(2026, 3, 26, 12, 0, tzinfo=timezone.utc)
    seed_task(task_id="task_completed", title="已完成任务", created_at=base_time, status=TaskStatus.COMPLETED)
    seed_task(
        task_id="task_failed",
        title="失败任务",
        created_at=base_time.replace(minute=1),
        status=TaskStatus.FAILED,
        result_status=ResultStatus.NOT_AVAILABLE,
    )

    response = client.get("/api/history", params={"status": "failed"})

    assert response.status_code == 200
    payload = response.json()
    assert [item["taskId"] for item in payload["data"]["items"]] == ["task_failed"]
    assert payload["data"]["items"][0]["status"] == "failed"


def test_get_history_supports_cursor_pagination() -> None:
    client = create_client()
    base_time = datetime(2026, 3, 26, 12, 0, tzinfo=timezone.utc)
    seed_task(task_id="task_a", title="任务 A", created_at=base_time)
    seed_task(task_id="task_b", title="任务 B", created_at=base_time.replace(minute=1))
    seed_task(task_id="task_c", title="任务 C", created_at=base_time.replace(minute=2))

    first_page = client.get("/api/history", params={"limit": 1})

    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert [item["taskId"] for item in first_payload["data"]["items"]] == ["task_c"]
    assert first_payload["meta"]["limit"] == 1
    assert first_payload["meta"]["nextCursor"] is not None
    assert "result" not in first_payload["data"]["items"][0]

    second_page = client.get(
        "/api/history",
        params={"limit": 1, "cursor": first_payload["meta"]["nextCursor"]},
    )

    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert [item["taskId"] for item in second_payload["data"]["items"]] == ["task_b"]
    assert second_payload["meta"]["nextCursor"] is not None


def test_get_history_rejects_invalid_status_filter() -> None:
    client = create_client()

    response = client.get("/api/history", params={"status": "blocked"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_get_history_rejects_limit_above_maximum() -> None:
    client = create_client()

    response = client.get("/api/history", params={"limit": 51})

    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_api_prompt_runtime_uses_file_runtime_for_primary_scope() -> None:
    runtime = ApiPromptRuntime()
    input_composition, evaluation_mode, provider_id, model_id = next(iter(PRIMARY_PROMPT_RUNTIME_SCOPES))

    resolved = runtime.resolve(
        stage="rubric_evaluation",
        input_composition=input_composition,
        evaluation_mode=evaluation_mode,
        provider_id=provider_id,
        model_id=model_id,
    )

    assert resolved.promptVersion == "v1"


def test_api_prompt_runtime_uses_fallback_for_non_primary_scope() -> None:
    runtime = ApiPromptRuntime()

    resolved = runtime.resolve(
        stage="rubric_evaluation",
        input_composition="outline_only",
        evaluation_mode="degraded",
        provider_id="provider-other",
        model_id="model-other",
    )

    assert resolved.promptVersion == "v1"
    assert resolved.schemaVersion == "1.0.0"
    assert resolved.rubricVersion == "rubric-v1"
