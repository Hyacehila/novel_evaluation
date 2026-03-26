from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from packages.schemas.common.enums import ResultStatus, TaskStatus
from packages.schemas.evals import EvalBaseline, EvalRecord, EvalReport, EvalReportType
from packages.schemas.output.error import ErrorCode

from evals.builders import (
    EvalBuildError,
    build_baseline,
    build_eval_case,
    build_eval_record,
    build_report,
    build_report_comparison,
)
from evals.loaders import load_dataset_entry, load_prompt_metadata_snapshot
from evals.models import RecordBuildInput
from evals.writers import EvalPathError, load_baseline, write_baseline, write_report


@dataclass(frozen=True)
class MinimalRunnerResult:
    task_id: str
    task_status: TaskStatus
    result_status: ResultStatus
    duration_ms: int
    schema_valid: bool
    error_code: ErrorCode | None = None
    error_message: str | None = None

    @classmethod
    def available(cls, *, task_id: str, duration_ms: int) -> "MinimalRunnerResult":
        return cls(
            task_id=task_id,
            task_status=TaskStatus.COMPLETED,
            result_status=ResultStatus.AVAILABLE,
            duration_ms=duration_ms,
            schema_valid=True,
        )

    @classmethod
    def blocked(
        cls,
        *,
        task_id: str,
        duration_ms: int,
        error_code: ErrorCode,
        error_message: str,
    ) -> "MinimalRunnerResult":
        return cls(
            task_id=task_id,
            task_status=TaskStatus.COMPLETED,
            result_status=ResultStatus.BLOCKED,
            duration_ms=duration_ms,
            schema_valid=False,
            error_code=error_code,
            error_message=error_message,
        )


@dataclass(frozen=True)
class MinimalRunnerCase:
    dataset_ref: str
    goal: str
    result: MinimalRunnerResult


@dataclass(frozen=True)
class MinimalRunnerOutcome:
    records: tuple[EvalRecord, ...]
    report: EvalReport
    baseline: EvalBaseline | None = None
    should_persist_baseline: bool = False


class MinimalEvalRunner:
    def __init__(self, *, evals_root: Path | str, prompts_root: Path | str) -> None:
        self._evals_root = Path(evals_root).resolve()
        self._prompts_root = Path(prompts_root).resolve()

    def run(
        self,
        *,
        cases: Iterable[MinimalRunnerCase],
        prompt_id: str,
        prompt_version: str,
        provider_id: str,
        model_id: str,
        report_id: str,
        created_at: str,
        baseline_id: str | None = None,
    ) -> MinimalRunnerOutcome:
        case_list = tuple(cases)
        if not case_list:
            raise ValueError("至少提供一个 case。")
        prompt_metadata = load_prompt_metadata_snapshot(
            prompts_root=self._prompts_root,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
        )
        eval_cases = tuple(
            build_eval_case(
                dataset_entry=load_dataset_entry(self._resolve_dataset_path(case.dataset_ref)),
                dataset_ref=case.dataset_ref,
                goal=case.goal,
            )
            for case in case_list
        )
        records = tuple(
            build_eval_record(
                build_input=RecordBuildInput(
                    evalCaseId=eval_case.caseId,
                    taskId=case.result.task_id,
                    taskStatus=case.result.task_status,
                    resultStatus=case.result.result_status,
                    errorCode=case.result.error_code,
                    errorMessage=case.result.error_message,
                    durationMs=case.result.duration_ms,
                    schemaValid=case.result.schema_valid,
                ),
                prompt_metadata=prompt_metadata,
                provider_id=provider_id,
                model_id=model_id,
            )
            for eval_case, case in zip(eval_cases, case_list, strict=True)
        )
        if baseline_id is None:
            report = build_report(
                report_id=report_id,
                report_type=EvalReportType.EXECUTION_SUMMARY,
                records=records,
                prompt_metadata=prompt_metadata,
                provider_id=provider_id,
                model_id=model_id,
                created_at=created_at,
            )
            return MinimalRunnerOutcome(records=records, report=report)

        baseline_path = self._evals_root / "baselines" / f"{baseline_id}.json"
        if baseline_path.exists():
            baseline = load_baseline(baseline_path)
            comparison = build_report_comparison(current_records=records, baseline=baseline)
            report = build_report(
                report_id=report_id,
                report_type=EvalReportType.BASELINE_COMPARISON,
                records=records,
                prompt_metadata=prompt_metadata,
                provider_id=provider_id,
                model_id=model_id,
                created_at=created_at,
                comparison=comparison,
            )
            return MinimalRunnerOutcome(
                records=records,
                report=report,
                baseline=baseline,
                should_persist_baseline=False,
            )

        baseline = build_baseline(
            baseline_id=baseline_id,
            cases=eval_cases,
            prompt_metadata=prompt_metadata,
            provider_id=provider_id,
            model_id=model_id,
            created_at=created_at,
            records=records,
        )
        report = build_report(
            report_id=report_id,
            report_type=EvalReportType.EXECUTION_SUMMARY,
            records=records,
            prompt_metadata=prompt_metadata,
            provider_id=provider_id,
            model_id=model_id,
            created_at=created_at,
        )
        return MinimalRunnerOutcome(
            records=records,
            report=report,
            baseline=baseline,
            should_persist_baseline=True,
        )

    def write_outputs(self, outcome: MinimalRunnerOutcome) -> tuple[Path | None, Path]:
        baseline_path = None
        if outcome.baseline is not None and outcome.should_persist_baseline:
            baseline_path = write_baseline(root=self._evals_root, baseline=outcome.baseline)
        report_path = write_report(root=self._evals_root, report=outcome.report)
        return baseline_path, report_path

    def _resolve_dataset_path(self, dataset_ref: str) -> Path:
        candidate_path = (self._evals_root / dataset_ref).resolve()
        try:
            candidate_path.relative_to(self._evals_root)
        except ValueError as error:
            raise EvalPathError(f"dataset_ref 超出 evals 根目录：{dataset_ref}") from error
        return candidate_path


__all__ = [
    "MinimalEvalRunner",
    "MinimalRunnerCase",
    "MinimalRunnerOutcome",
    "MinimalRunnerResult",
    "EvalBuildError",
]
