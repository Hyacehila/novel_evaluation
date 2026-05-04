from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from api import dependencies as api_dependencies
from provider_adapters import LocalDeterministicProviderAdapter
from tests.test_api import create_client
from packages.schemas.input.joint_submission import JointSubmissionRequest


LONG_OPENING_OUTLINE = "long_opening_outline"
COMPLETED_FULLTEXT = "completed_fulltext"


@pytest.fixture(autouse=True)
def configure_fake_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(
        api_dependencies,
        "build_configured_provider_adapter",
        lambda *, api_key: LocalDeterministicProviderAdapter(
            provider_id="provider-deepseek",
            model_id="deepseek-v4-pro",
            structured_stage_outputs=True,
        ),
    )


def build_submission_payload(
    *,
    analysis_mode: str,
    chapters: list[dict[str, str]] | None = None,
    outline: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": "双模式契约测试",
        "analysisMode": analysis_mode,
        "sourceType": "direct_input",
    }
    if chapters is not None:
        payload["chapters"] = chapters
    if outline is not None:
        payload["outline"] = outline
    return payload


def test_joint_submission_accepts_long_opening_outline_mode() -> None:
    request = JointSubmissionRequest.model_validate(
        build_submission_payload(
            analysis_mode=LONG_OPENING_OUTLINE,
            chapters=[{"title": "第一章", "content": "开篇正文内容"}],
            outline={"content": "长篇大纲内容"},
        )
    )

    assert request.analysisMode == LONG_OPENING_OUTLINE
    assert request.hasChapters is True
    assert request.hasOutline is True


def test_joint_submission_accepts_completed_fulltext_mode_without_outline() -> None:
    request = JointSubmissionRequest.model_validate(
        build_submission_payload(
            analysis_mode=COMPLETED_FULLTEXT,
            chapters=[{"title": "全文", "content": "已经完结的全文内容"}],
        )
    )

    assert request.analysisMode == COMPLETED_FULLTEXT
    assert request.hasChapters is True
    assert request.hasOutline is False


@pytest.mark.parametrize(
    "payload",
    [
        build_submission_payload(
            analysis_mode=LONG_OPENING_OUTLINE,
            outline={"content": "只有大纲，缺少开篇正文"},
        ),
        build_submission_payload(
            analysis_mode=LONG_OPENING_OUTLINE,
            chapters=[{"title": "第一章", "content": "只有开篇正文，缺少大纲"}],
        ),
        build_submission_payload(
            analysis_mode=COMPLETED_FULLTEXT,
            outline={"content": "只有大纲，缺少全文正文"},
        ),
        build_submission_payload(
            analysis_mode=COMPLETED_FULLTEXT,
            chapters=[{"title": "全文", "content": "已经完结的全文内容"}],
            outline={"content": "全文模式不允许再携带大纲"},
        ),
    ],
)
def test_joint_submission_rejects_analysis_mode_shape_conflicts(payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        JointSubmissionRequest.model_validate(payload)


def test_post_tasks_creates_long_opening_outline_task() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        json=build_submission_payload(
            analysis_mode=LONG_OPENING_OUTLINE,
            chapters=[{"title": "第一章", "content": "开篇正文内容"}],
            outline={"content": "长篇大纲内容"},
        ),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["analysisMode"] == LONG_OPENING_OUTLINE
    assert payload["data"]["status"] == "queued"
    assert payload["data"]["resultStatus"] == "not_available"


def test_post_tasks_creates_completed_fulltext_task_without_outline() -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        json=build_submission_payload(
            analysis_mode=COMPLETED_FULLTEXT,
            chapters=[{"title": "全文", "content": "已经完结的全文内容"}],
        ),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["analysisMode"] == COMPLETED_FULLTEXT
    assert payload["data"]["hasChapters"] is True
    assert payload["data"]["hasOutline"] is False


@pytest.mark.parametrize(
    "payload",
    [
        build_submission_payload(
            analysis_mode=LONG_OPENING_OUTLINE,
            outline={"content": "只有大纲，缺少开篇正文"},
        ),
        build_submission_payload(
            analysis_mode=LONG_OPENING_OUTLINE,
            chapters=[{"title": "第一章", "content": "只有开篇正文，缺少大纲"}],
        ),
        build_submission_payload(
            analysis_mode=COMPLETED_FULLTEXT,
            outline={"content": "只有大纲，缺少全文正文"},
        ),
        build_submission_payload(
            analysis_mode=COMPLETED_FULLTEXT,
            chapters=[{"title": "全文", "content": "已经完结的全文内容"}],
            outline={"content": "全文模式不允许再携带大纲"},
        ),
    ],
)
def test_post_tasks_rejects_analysis_mode_shape_conflicts(payload: dict[str, Any]) -> None:
    client = create_client()

    response = client.post(
        "/api/tasks",
        content=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
    envelope = response.json()
    assert envelope["success"] is False
    assert envelope["error"]["code"] == "VALIDATION_ERROR"


def test_prompt_runtime_primary_scopes_are_explicit_analysis_modes() -> None:
    from api.dependencies import PRIMARY_PROMPT_RUNTIME_SCOPES

    assert PRIMARY_PROMPT_RUNTIME_SCOPES
    assert {scope[1] for scope in PRIMARY_PROMPT_RUNTIME_SCOPES} == {
        LONG_OPENING_OUTLINE,
        COMPLETED_FULLTEXT,
    }
