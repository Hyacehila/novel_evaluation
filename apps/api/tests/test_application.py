from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.application.services.evaluation_service import EvaluationService
from packages.application.ports.task_repository import InMemoryTaskRepository
from packages.application.support.id_generator import StaticIdGenerator, UuidTaskIdGenerator
from packages.application.support.clock import FixedClock
from packages.schemas.common.enums import EvaluationMode, ResultStatus, SubmissionSourceType, TaskStatus
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline
from packages.schemas.output.error import ErrorCode


def build_request(*, chapters: bool = True, outline: bool = True) -> JointSubmissionRequest:
    return JointSubmissionRequest(
        title="测试稿件",
        chapters=[ManuscriptChapter(content="第一章内容", title="第一章")] if chapters else None,
        outline=ManuscriptOutline(content="大纲内容") if outline else None,
        sourceType=SubmissionSourceType.DIRECT_INPUT,
    )


def build_service() -> EvaluationService:
    return EvaluationService(
        task_repository=InMemoryTaskRepository(),
        id_generator=StaticIdGenerator("task_20260325_001"),
        clock=FixedClock(datetime(2026, 3, 25, 0, 0, tzinfo=timezone.utc)),
    )


def test_create_task_starts_in_queued_not_available() -> None:
    service = build_service()
    task = service.create_task(build_request())

    assert task.taskId == "task_20260325_001"
    assert task.status is TaskStatus.QUEUED
    assert task.resultStatus is ResultStatus.NOT_AVAILABLE
    assert task.resultAvailable is False
    assert task.evaluationMode is EvaluationMode.FULL


def test_create_task_uses_degraded_mode_for_partial_input() -> None:
    service = build_service()
    task = service.create_task(build_request(chapters=False, outline=True))

    assert task.evaluationMode is EvaluationMode.DEGRADED


def test_start_task_moves_to_processing() -> None:
    service = build_service()
    task = service.create_task(build_request())

    updated = service.start_task(task.taskId)

    assert updated.status is TaskStatus.PROCESSING
    assert updated.startedAt is not None


def test_complete_task_with_result_moves_to_available() -> None:
    service = build_service()
    task = service.create_task(build_request())
    service.start_task(task.taskId)

    updated = service.complete_task_with_result(
        task.taskId,
        signing_probability=80,
        commercial_value=78,
        writing_quality=76,
        innovation_score=74,
    )

    assert updated.status is TaskStatus.COMPLETED
    assert updated.resultStatus is ResultStatus.AVAILABLE
    result_resource = service.get_result(task.taskId)
    assert result_resource.result is not None
    assert result_resource.result.taskId == task.taskId
    assert result_resource.resultTime is not None
    assert result_resource.result.signingProbability == 80


def test_block_task_moves_to_completed_blocked() -> None:
    service = build_service()
    task = service.create_task(build_request(chapters=False, outline=True))
    service.start_task(task.taskId)

    updated = service.block_task(
        task.taskId,
        error_code=ErrorCode.INSUFFICIENT_OUTLINE_INPUT,
        error_message="输入未满足正式展示条件",
    )

    assert updated.status is TaskStatus.COMPLETED
    assert updated.resultStatus is ResultStatus.BLOCKED
    result_resource = service.get_result(task.taskId)
    assert result_resource.result is None
    assert result_resource.message == "结果未满足正式展示条件"


def test_fail_task_moves_to_failed_not_available() -> None:
    service = build_service()
    task = service.create_task(build_request())
    service.start_task(task.taskId)

    updated = service.fail_task(
        task.taskId,
        error_code=ErrorCode.INTERNAL_ERROR,
        error_message="服务暂时不可用",
    )

    assert updated.status is TaskStatus.FAILED
    assert updated.resultStatus is ResultStatus.NOT_AVAILABLE
    result_resource = service.get_result(task.taskId)
    assert result_resource.result is None
    assert result_resource.message == "结果尚未生成或当前不可展示"


def test_get_history_limits_items_to_20() -> None:
    service = EvaluationService(
        task_repository=InMemoryTaskRepository(),
        id_generator=UuidTaskIdGenerator(),
        clock=FixedClock(datetime(2026, 3, 25, 0, 0, tzinfo=timezone.utc)),
    )

    for _ in range(25):
        service.create_task(build_request())

    history = service.get_history()

    assert len(history.items) == 20
    assert history.meta is not None
    assert history.meta.limit == 20


def test_get_missing_task_raises_lookup_error() -> None:
    service = build_service()

    with pytest.raises(LookupError):
        service.get_task("missing")


def test_cannot_start_terminal_task_again() -> None:
    service = build_service()
    task = service.create_task(build_request())
    service.start_task(task.taskId)
    service.fail_task(
        task.taskId,
        error_code=ErrorCode.INTERNAL_ERROR,
        error_message="服务暂时不可用",
    )

    with pytest.raises(ValueError):
        service.start_task(task.taskId)
