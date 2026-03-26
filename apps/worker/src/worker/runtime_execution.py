from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evals.loaders import load_dataset_entry
from evals.runners.minimal_runner import MinimalEvalRunner, MinimalRunnerCase, MinimalRunnerResult
from evals.writers import write_records
from packages.application.ports.task_repository import InMemoryTaskRepository
from packages.application.services.evaluation_service import EvaluationService
from packages.application.support.clock import UtcClock
from packages.application.support.id_generator import StaticIdGenerator
from packages.schemas.common.enums import ResultStatus, SubmissionSourceType, TaskStatus
from packages.schemas.input.joint_submission import JointSubmissionRequest
from packages.schemas.input.manuscript import ManuscriptChapter, ManuscriptOutline

from worker.bootstrap import WorkerRuntimeContext


@dataclass(frozen=True, slots=True)
class BatchExecutionSummary:
    total_count: int
    available_count: int
    blocked_count: int
    failed_count: int
    report_path: Path | None = None


def resolve_suite_path(*, evals_root: Path, suite_name: str) -> Path:
    direct = Path(suite_name)
    if direct.exists():
        return direct.resolve()
    candidate = evals_root / "cases" / f"{suite_name}.json"
    return candidate.resolve()


def load_suite(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_submission_from_dataset(*, evals_root: Path, dataset_ref: str) -> JointSubmissionRequest:
    entry = load_dataset_entry(evals_root / dataset_ref)
    chapters_content = _resolve_content(evals_root=evals_root, inline_value=entry.chaptersContent, ref_value=entry.chaptersRef)
    outline_content = _resolve_content(evals_root=evals_root, inline_value=entry.outlineContent, ref_value=entry.outlineRef)
    return JointSubmissionRequest(
        title=entry.title,
        chapters=[ManuscriptChapter(title=entry.title, content=chapters_content)] if chapters_content is not None else None,
        outline=ManuscriptOutline(content=outline_content) if outline_content is not None else None,
        sourceType=SubmissionSourceType.HISTORY_DERIVED,
    )


def evaluate_submission(
    *,
    context: WorkerRuntimeContext,
    submission: JointSubmissionRequest,
    task_id: str,
) -> tuple[Any, Any]:
    service = EvaluationService(
        task_repository=InMemoryTaskRepository(),
        prompt_runtime=context.prompt_runtime,
        provider_adapter=context.provider_adapter,
        id_generator=StaticIdGenerator(task_id),
        clock=UtcClock(),
    )
    task = service.create_task(submission)
    service.execute_task(task.taskId, submission)
    return service.get_task(task.taskId), service.get_result(task.taskId)


def build_runner_cases_from_suite(*, context: WorkerRuntimeContext, suite: dict[str, Any]) -> tuple[MinimalRunnerCase, ...]:
    cases: list[MinimalRunnerCase] = []
    for index, case in enumerate(suite.get("cases", []), start=1):
        dataset_ref = str(case["datasetRef"])
        goal = str(case["goal"])
        submission = build_submission_from_dataset(evals_root=context.evals_root, dataset_ref=dataset_ref)
        task_id = f"task_eval_{index:03d}"
        task, result = evaluate_submission(context=context, submission=submission, task_id=task_id)
        cases.append(
            MinimalRunnerCase(
                dataset_ref=dataset_ref,
                goal=goal,
                result=_to_runner_result(task=task, result=result),
            )
        )
    return tuple(cases)


def run_eval_suite(
    *,
    context: WorkerRuntimeContext,
    suite_path: Path,
    report_id: str,
    baseline_id: str | None,
) -> tuple[Path | None, Path, Path]:
    suite = load_suite(suite_path)
    cases = build_runner_cases_from_suite(context=context, suite=suite)
    prompt_id = str(suite.get("promptId", "screening-default"))
    prompt_version = str(suite.get("promptVersion", "v1"))
    runner = MinimalEvalRunner(evals_root=context.evals_root, prompts_root=context.prompts_root)
    outcome = runner.run(
        cases=cases,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
        provider_id=context.provider_adapter.provider_id,
        model_id=context.provider_adapter.model_id,
        report_id=report_id,
        baseline_id=baseline_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    baseline_path, report_path = runner.write_outputs(outcome)
    records_path = write_records(root=context.evals_root, report_id=outcome.report.reportId, records=outcome.records)
    return baseline_path, report_path, records_path


def run_batch_source(
    *,
    context: WorkerRuntimeContext,
    source_path: Path,
    report_id: str | None,
) -> BatchExecutionSummary:
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    submissions = payload["submissions"] if isinstance(payload, dict) else payload
    tasks = [
        JointSubmissionRequest.model_validate(submission)
        for submission in submissions
    ]
    available_count = 0
    blocked_count = 0
    failed_count = 0
    for index, submission in enumerate(tasks, start=1):
        task, result = evaluate_submission(
            context=context,
            submission=submission,
            task_id=f"task_batch_{index:03d}",
        )
        if task.resultStatus is ResultStatus.AVAILABLE:
            available_count += 1
        elif task.resultStatus is ResultStatus.BLOCKED:
            blocked_count += 1
        else:
            failed_count += 1
        del result

    report_path = None
    if report_id:
        report_path = context.repo_root / "output" / "batch" / f"{report_id}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "reportId": report_id,
                    "totalCount": len(tasks),
                    "availableCount": available_count,
                    "blockedCount": blocked_count,
                    "failedCount": failed_count,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return BatchExecutionSummary(
        total_count=len(tasks),
        available_count=available_count,
        blocked_count=blocked_count,
        failed_count=failed_count,
        report_path=report_path,
    )


def build_default_report_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"


def _resolve_content(*, evals_root: Path, inline_value: str | None, ref_value: str | None) -> str | None:
    if inline_value is not None:
        return inline_value
    if ref_value is None:
        return None
    path = (evals_root / ref_value).resolve()
    path.relative_to(evals_root.resolve())
    return path.read_text(encoding="utf-8")


def _to_runner_result(*, task, result) -> MinimalRunnerResult:
    duration_ms = 5
    if task.status is TaskStatus.COMPLETED and task.resultStatus is ResultStatus.AVAILABLE:
        return MinimalRunnerResult.available(task_id=task.taskId, duration_ms=duration_ms)
    if task.status is TaskStatus.COMPLETED and task.resultStatus is ResultStatus.BLOCKED:
        return MinimalRunnerResult.blocked(
            task_id=task.taskId,
            duration_ms=duration_ms,
            error_code=task.errorCode,
            error_message=task.errorMessage or (result.message or "业务阻断"),
        )
    return MinimalRunnerResult(
        task_id=task.taskId,
        task_status=task.status,
        result_status=task.resultStatus,
        duration_ms=duration_ms,
        schema_valid=False,
        error_code=task.errorCode,
        error_message=task.errorMessage or result.message,
    )
