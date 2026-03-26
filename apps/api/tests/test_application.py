from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from packages.application.ports.task_repository import InMemoryTaskRepository
from packages.application.services.evaluation_service import EvaluationService
from packages.application.support.clock import FixedClock
from packages.application.support.id_generator import StaticIdGenerator, UuidTaskIdGenerator
from packages.schemas.common.enums import (
    EvaluationMode,
    InputComposition,
    ResultStatus,
    StageName,
    SubmissionSourceType,
    TaskStatus,
)
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline
from packages.schemas.output.error import ErrorCode
from packages.schemas.output.task import EvaluationTask


@dataclass(frozen=True, slots=True)
class StubResolvedPrompt:
    promptVersion: str = "prompt-test-v1"
    schemaVersion: str = "schema-test-v1"
    rubricVersion: str = "rubric-test-v1"


@dataclass(frozen=True, slots=True)
class StubProviderAdapter:
    provider_id: str = "provider-test"
    model_id: str = "model-test"


@dataclass(frozen=True, slots=True)
class StubPromptRuntime:
    resolved_prompt: StubResolvedPrompt = StubResolvedPrompt()
    expected_stage: str | None = None
    expected_input_composition: str | None = None
    expected_evaluation_mode: str | None = None
    expected_provider_id: str | None = None
    expected_model_id: str | None = None

    def resolve(
        self,
        *,
        stage: str,
        input_composition: str,
        evaluation_mode: str,
        provider_id: str,
        model_id: str,
    ) -> StubResolvedPrompt:
        if self.expected_stage is not None:
            assert stage == self.expected_stage
        if self.expected_input_composition is not None:
            assert input_composition == self.expected_input_composition
        if self.expected_evaluation_mode is not None:
            assert evaluation_mode == self.expected_evaluation_mode
        if self.expected_provider_id is not None:
            assert provider_id == self.expected_provider_id
        if self.expected_model_id is not None:
            assert model_id == self.expected_model_id
        return self.resolved_prompt


def build_request(*, chapters: bool = True, outline: bool = True) -> JointSubmissionRequest:
    return JointSubmissionRequest(
        title="测试稿件",
        chapters=[ManuscriptChapter(content="第一章内容", title="第一章")] if chapters else None,
        outline=ManuscriptOutline(content="大纲内容") if outline else None,
        sourceType=SubmissionSourceType.DIRECT_INPUT,
    )


def build_service(
    *,
    task_repository: InMemoryTaskRepository | None = None,
    prompt_runtime: StubPromptRuntime | None = None,
    provider_adapter: StubProviderAdapter | None = None,
    id_generator: StaticIdGenerator | UuidTaskIdGenerator | None = None,
    clock: FixedClock | None = None,
) -> EvaluationService:
    resolved_provider_adapter = provider_adapter or StubProviderAdapter()
    resolved_prompt_runtime = prompt_runtime or StubPromptRuntime(
        expected_provider_id=resolved_provider_adapter.provider_id,
        expected_model_id=resolved_provider_adapter.model_id,
    )
    return EvaluationService(
        task_repository=task_repository or InMemoryTaskRepository(),
        prompt_runtime=resolved_prompt_runtime,
        provider_adapter=resolved_provider_adapter,
        id_generator=id_generator or StaticIdGenerator("task_20260325_001"),
        clock=clock or FixedClock(datetime(2026, 3, 25, 0, 0, tzinfo=timezone.utc)),
    )


def test_create_task_starts_in_queued_not_available() -> None:
    service = build_service()
    task = service.create_task(build_request())

    assert task.taskId == "task_20260325_001"
    assert task.status is TaskStatus.QUEUED
    assert task.resultStatus is ResultStatus.NOT_AVAILABLE
    assert task.resultAvailable is False
    assert task.evaluationMode is EvaluationMode.FULL


def test_create_task_reads_runtime_metadata_from_collaborators() -> None:
    prompt_runtime = StubPromptRuntime(
        resolved_prompt=StubResolvedPrompt(
            promptVersion="prompt-screening-v2",
            schemaVersion="schema-2026.03",
            rubricVersion="rubric-2026.03",
        ),
        expected_stage=StageName.INPUT_SCREENING.value,
        expected_input_composition=InputComposition.CHAPTERS_OUTLINE.value,
        expected_evaluation_mode=EvaluationMode.FULL.value,
        expected_provider_id="provider-runtime",
        expected_model_id="model-runtime",
    )
    service = build_service(
        prompt_runtime=prompt_runtime,
        provider_adapter=StubProviderAdapter(
            provider_id="provider-runtime",
            model_id="model-runtime",
        ),
    )

    task = service.create_task(build_request())

    assert task.schemaVersion == "schema-2026.03"
    assert task.promptVersion == "prompt-screening-v2"
    assert task.rubricVersion == "rubric-2026.03"
    assert task.providerId == "provider-runtime"
    assert task.modelId == "model-runtime"


def test_create_task_uses_degraded_mode_for_partial_input() -> None:
    service = build_service(
        prompt_runtime=StubPromptRuntime(
            expected_stage=StageName.INPUT_SCREENING.value,
            expected_input_composition=InputComposition.OUTLINE_ONLY.value,
            expected_evaluation_mode=EvaluationMode.DEGRADED.value,
            expected_provider_id="provider-test",
            expected_model_id="model-test",
        )
    )

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


def test_complete_task_with_result_keeps_task_runtime_metadata_in_result() -> None:
    service = build_service(
        prompt_runtime=StubPromptRuntime(
            resolved_prompt=StubResolvedPrompt(
                promptVersion="prompt-result-v3",
                schemaVersion="schema-3.0.0",
                rubricVersion="rubric-3.0.0",
            )
        ),
        provider_adapter=StubProviderAdapter(
            provider_id="provider-result",
            model_id="model-result",
        ),
    )
    task = service.create_task(build_request())
    service.start_task(task.taskId)

    service.complete_task_with_result(
        task.taskId,
        signing_probability=80,
        commercial_value=78,
        writing_quality=76,
        innovation_score=74,
    )

    result = service.get_result(task.taskId).result

    assert result is not None
    assert result.schemaVersion == "schema-3.0.0"
    assert result.promptVersion == "prompt-result-v3"
    assert result.rubricVersion == "rubric-3.0.0"
    assert result.providerId == "provider-result"
    assert result.modelId == "model-result"


def test_complete_task_with_result_resolves_missing_runtime_metadata_from_collaborators() -> None:
    repository = InMemoryTaskRepository()
    service = build_service(
        task_repository=repository,
        prompt_runtime=StubPromptRuntime(
            resolved_prompt=StubResolvedPrompt(
                promptVersion="prompt-fallback-v2",
                schemaVersion="schema-fallback-v2",
                rubricVersion="rubric-fallback-v2",
            ),
            expected_stage=StageName.INPUT_SCREENING.value,
            expected_input_composition=InputComposition.CHAPTERS_OUTLINE.value,
            expected_evaluation_mode=EvaluationMode.FULL.value,
            expected_provider_id="provider-fallback",
            expected_model_id="model-fallback",
        ),
        provider_adapter=StubProviderAdapter(
            provider_id="provider-fallback",
            model_id="model-fallback",
        ),
    )
    task = EvaluationTask(
        taskId="legacy_task",
        title="历史任务",
        inputSummary="已提交 1 章正文和 1 份大纲",
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        hasChapters=True,
        hasOutline=True,
        evaluationMode=EvaluationMode.FULL,
        status=TaskStatus.PROCESSING,
        resultStatus=ResultStatus.NOT_AVAILABLE,
        createdAt=datetime(2026, 3, 25, 0, 0, tzinfo=timezone.utc),
        startedAt=datetime(2026, 3, 25, 0, 0, tzinfo=timezone.utc),
        updatedAt=datetime(2026, 3, 25, 0, 0, tzinfo=timezone.utc),
    )
    repository.create_task(task)

    service.complete_task_with_result(
        task.taskId,
        signing_probability=80,
        commercial_value=78,
        writing_quality=76,
        innovation_score=74,
    )

    result = service.get_result(task.taskId).result

    assert result is not None
    assert result.schemaVersion == "schema-fallback-v2"
    assert result.promptVersion == "prompt-fallback-v2"
    assert result.rubricVersion == "rubric-fallback-v2"
    assert result.providerId == "provider-fallback"
    assert result.modelId == "model-fallback"


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
    service = build_service(id_generator=UuidTaskIdGenerator())

    for _ in range(25):
        service.create_task(build_request())

    history = service.get_history()

    assert len(history.items) == 20
    assert history.meta is not None
    assert history.meta.limit == 20


def test_get_history_filters_by_title_status_and_cursor() -> None:
    repository = InMemoryTaskRepository()
    first_time = datetime(2026, 3, 25, 0, 0, tzinfo=timezone.utc)
    second_time = datetime(2026, 3, 25, 0, 1, tzinfo=timezone.utc)
    third_time = datetime(2026, 3, 25, 0, 2, tzinfo=timezone.utc)
    repository.create_task(
        EvaluationTask(
            taskId="task_a",
            title="星际序章",
            inputSummary="已提交 1 章正文和 1 份大纲",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            hasChapters=True,
            hasOutline=True,
            evaluationMode=EvaluationMode.FULL,
            status=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.AVAILABLE,
            createdAt=first_time,
            startedAt=first_time,
            completedAt=first_time,
            updatedAt=first_time,
        )
    )
    repository.create_task(
        EvaluationTask(
            taskId="task_b",
            title="都市片段",
            inputSummary="已提交 1 章正文和 1 份大纲",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            hasChapters=True,
            hasOutline=True,
            evaluationMode=EvaluationMode.FULL,
            status=TaskStatus.FAILED,
            resultStatus=ResultStatus.NOT_AVAILABLE,
            errorCode=ErrorCode.INTERNAL_ERROR,
            errorMessage="服务暂时不可用",
            createdAt=second_time,
            startedAt=second_time,
            completedAt=second_time,
            updatedAt=second_time,
        )
    )
    repository.create_task(
        EvaluationTask(
            taskId="task_c",
            title="星际终章",
            inputSummary="已提交 1 章正文和 1 份大纲",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            hasChapters=True,
            hasOutline=True,
            evaluationMode=EvaluationMode.FULL,
            status=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.AVAILABLE,
            createdAt=third_time,
            startedAt=third_time,
            completedAt=third_time,
            updatedAt=third_time,
        )
    )
    service = build_service(task_repository=repository)

    filtered = service.get_history(q="星际", status=TaskStatus.COMPLETED, limit=1)

    assert [item.taskId for item in filtered.items] == ["task_c"]
    assert filtered.meta is not None
    assert filtered.meta.nextCursor is not None

    next_page = service.get_history(
        q="星际",
        status=TaskStatus.COMPLETED,
        limit=1,
        cursor=filtered.meta.nextCursor,
    )

    assert [item.taskId for item in next_page.items] == ["task_a"]
    assert next_page.meta is not None
    assert next_page.meta.nextCursor is None


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



def test_recover_incomplete_tasks_marks_queued_and_processing_failed() -> None:
    service = build_service(id_generator=StaticIdGenerator("task_recovery_a"))
    queued_task = service.create_task(build_request())

    processing_service = build_service(
        task_repository=service._task_repository,
        id_generator=StaticIdGenerator("task_recovery_b"),
    )
    processing_task = processing_service.create_task(build_request())
    processing_service.start_task(processing_task.taskId)

    service.recover_incomplete_tasks()

    recovered_queued = service.get_task(queued_task.taskId)
    recovered_processing = service.get_task(processing_task.taskId)
    assert recovered_queued.status is TaskStatus.FAILED
    assert recovered_queued.resultStatus is ResultStatus.NOT_AVAILABLE
    assert recovered_processing.status is TaskStatus.FAILED
    assert recovered_processing.resultStatus is ResultStatus.NOT_AVAILABLE
    assert service.get_result(queued_task.taskId).result is None
    assert service.get_result(processing_task.taskId).result is None
