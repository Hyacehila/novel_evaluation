from __future__ import annotations

import pytest

from packages.schemas.common.enums import InputComposition, ResultStatus, TaskStatus
from packages.schemas.output.error import ErrorCode
from packages.schemas.evals import EvalExpectedOutcomeType, EvalReportType

from evals.builders import (
    EvalBuildError,
    build_baseline,
    build_eval_case,
    build_eval_record,
    build_execution_summary,
    build_report,
    build_report_comparison,
)
from evals.models import EvalDatasetEntry, PromptMetadataSnapshot, RecordBuildInput


PROMPT_METADATA = PromptMetadataSnapshot(
    promptId="screening-default",
    promptVersion="v1",
    stage="input_screening",
    schemaVersion="1.0.0",
    rubricVersion="rubric-v1",
    registryStatus="candidate",
    versionStatus="candidate",
    enabled=True,
)


def build_dataset_entry(*, case_id: str = "case_001", included_in_baseline: bool = True) -> EvalDatasetEntry:
    return EvalDatasetEntry(
        caseId=case_id,
        title="测试样本",
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        chaptersRef="datasets/fixtures/case_001-chapters.md",
        outlineRef="datasets/fixtures/case_001-outline.md",
        expectedOutcomeType=EvalExpectedOutcomeType.AVAILABLE,
        includedInBaseline=included_in_baseline,
        notes="最小样本",
    )


def test_build_eval_case_projects_dataset_entry() -> None:
    case = build_eval_case(
        dataset_entry=build_dataset_entry(),
        dataset_ref="datasets/scoring/case_001.json",
        goal="验证最小回归样本可生成 EvalCase",
    )

    assert case.caseId == "case_001"
    assert case.datasetRef == "datasets/scoring/case_001.json"
    assert case.expectedOutcomeType is EvalExpectedOutcomeType.AVAILABLE
    assert case.includedInBaseline is True


def test_build_eval_record_projects_available_result() -> None:
    record = build_eval_record(
        build_input=RecordBuildInput(
            evalCaseId="case_001",
            taskId="task_001",
            taskStatus=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.AVAILABLE,
            durationMs=1234,
            schemaValid=True,
        ),
        prompt_metadata=PROMPT_METADATA,
        provider_id="provider-local",
        model_id="model-local",
    )

    assert record.promptVersion == "v1"
    assert record.schemaValid is True
    assert record.resultStatus is ResultStatus.AVAILABLE


def test_build_execution_summary_counts_terminal_records() -> None:
    records = (
        build_eval_record(
            build_input=RecordBuildInput(
                evalCaseId="case_001",
                taskId="task_001",
                taskStatus=TaskStatus.COMPLETED,
                resultStatus=ResultStatus.AVAILABLE,
                durationMs=100,
                schemaValid=True,
            ),
            prompt_metadata=PROMPT_METADATA,
            provider_id="provider-local",
            model_id="model-local",
        ),
        build_eval_record(
            build_input=RecordBuildInput(
                evalCaseId="case_002",
                taskId="task_002",
                taskStatus=TaskStatus.COMPLETED,
                resultStatus=ResultStatus.BLOCKED,
                errorCode=ErrorCode.RESULT_BLOCKED,
                errorMessage="业务阻断",
                durationMs=200,
                schemaValid=False,
            ),
            prompt_metadata=PROMPT_METADATA,
            provider_id="provider-local",
            model_id="model-local",
        ),
        build_eval_record(
            build_input=RecordBuildInput(
                evalCaseId="case_003",
                taskId="task_003",
                taskStatus=TaskStatus.FAILED,
                resultStatus=ResultStatus.NOT_AVAILABLE,
                errorCode=ErrorCode.TIMEOUT,
                errorMessage="调用超时",
                durationMs=300,
                schemaValid=False,
            ),
            prompt_metadata=PROMPT_METADATA,
            provider_id="provider-local",
            model_id="model-local",
        ),
    )

    summary = build_execution_summary(records)

    assert summary.totalCount == 3
    assert summary.availableCount == 1
    assert summary.blockedCount == 1
    assert summary.failedCount == 1
    assert summary.schemaValidCount == 1


def test_build_baseline_only_includes_baseline_cases() -> None:
    baseline = build_baseline(
        baseline_id="baseline_v1",
        cases=(
            build_eval_case(
                dataset_entry=build_dataset_entry(case_id="case_001", included_in_baseline=True),
                dataset_ref="datasets/scoring/case_001.json",
                goal="case 1",
            ),
            build_eval_case(
                dataset_entry=build_dataset_entry(case_id="case_002", included_in_baseline=False),
                dataset_ref="datasets/scoring/case_002.json",
                goal="case 2",
            ),
        ),
        prompt_metadata=PROMPT_METADATA,
        provider_id="provider-local",
        model_id="model-local",
        created_at="2026-03-26T00:00:00Z",
        records=(
            build_eval_record(
                build_input=RecordBuildInput(
                    evalCaseId="case_001",
                    taskId="task_001",
                    taskStatus=TaskStatus.COMPLETED,
                    resultStatus=ResultStatus.AVAILABLE,
                    durationMs=100,
                    schemaValid=True,
                ),
                prompt_metadata=PROMPT_METADATA,
                provider_id="provider-local",
                model_id="model-local",
            ),
            build_eval_record(
                build_input=RecordBuildInput(
                    evalCaseId="case_002",
                    taskId="task_002",
                    taskStatus=TaskStatus.COMPLETED,
                    resultStatus=ResultStatus.BLOCKED,
                    errorCode=ErrorCode.RESULT_BLOCKED,
                    errorMessage="业务阻断",
                    durationMs=200,
                    schemaValid=False,
                ),
                prompt_metadata=PROMPT_METADATA,
                provider_id="provider-local",
                model_id="model-local",
            ),
        ),
    )

    assert baseline.caseIds == ("case_001",)
    assert baseline.summary.totalCount == 1
    assert baseline.summary.availableCount == 1


def test_build_baseline_rejects_missing_baseline_record() -> None:
    with pytest.raises(EvalBuildError, match="缺少对应 record"):
        build_baseline(
            baseline_id="baseline_v1",
            cases=(
                build_eval_case(
                    dataset_entry=build_dataset_entry(case_id="case_001", included_in_baseline=True),
                    dataset_ref="datasets/scoring/case_001.json",
                    goal="case 1",
                ),
                build_eval_case(
                    dataset_entry=build_dataset_entry(case_id="case_002", included_in_baseline=True),
                    dataset_ref="datasets/scoring/case_002.json",
                    goal="case 2",
                ),
            ),
            prompt_metadata=PROMPT_METADATA,
            provider_id="provider-local",
            model_id="model-local",
            created_at="2026-03-26T00:00:00Z",
            records=(
                build_eval_record(
                    build_input=RecordBuildInput(
                        evalCaseId="case_001",
                        taskId="task_001",
                        taskStatus=TaskStatus.COMPLETED,
                        resultStatus=ResultStatus.AVAILABLE,
                        durationMs=100,
                        schemaValid=True,
                    ),
                    prompt_metadata=PROMPT_METADATA,
                    provider_id="provider-local",
                    model_id="model-local",
                ),
            ),
        )


def test_build_report_comparison_uses_current_summary_delta() -> None:
    records = (
        build_eval_record(
            build_input=RecordBuildInput(
                evalCaseId="case_001",
                taskId="task_001",
                taskStatus=TaskStatus.COMPLETED,
                resultStatus=ResultStatus.AVAILABLE,
                durationMs=100,
                schemaValid=True,
            ),
            prompt_metadata=PROMPT_METADATA,
            provider_id="provider-local",
            model_id="model-local",
        ),
        build_eval_record(
            build_input=RecordBuildInput(
                evalCaseId="case_002",
                taskId="task_002",
                taskStatus=TaskStatus.COMPLETED,
                resultStatus=ResultStatus.BLOCKED,
                errorCode=ErrorCode.RESULT_BLOCKED,
                errorMessage="业务阻断",
                durationMs=200,
                schemaValid=False,
            ),
            prompt_metadata=PROMPT_METADATA,
            provider_id="provider-local",
            model_id="model-local",
        ),
    )
    baseline = build_baseline(
        baseline_id="baseline_v1",
        cases=(
            build_eval_case(
                dataset_entry=build_dataset_entry(case_id="case_001", included_in_baseline=True),
                dataset_ref="datasets/scoring/case_001.json",
                goal="case 1",
            ),
            build_eval_case(
                dataset_entry=build_dataset_entry(case_id="case_002", included_in_baseline=True),
                dataset_ref="datasets/scoring/case_002.json",
                goal="case 2",
            ),
        ),
        prompt_metadata=PROMPT_METADATA,
        provider_id="provider-local",
        model_id="model-local",
        created_at="2026-03-25T00:00:00Z",
        records=(
            build_eval_record(
                build_input=RecordBuildInput(
                    evalCaseId="case_001",
                    taskId="task_001_old",
                    taskStatus=TaskStatus.COMPLETED,
                    resultStatus=ResultStatus.AVAILABLE,
                    durationMs=100,
                    schemaValid=True,
                ),
                prompt_metadata=PROMPT_METADATA,
                provider_id="provider-local",
                model_id="model-local",
            ),
            build_eval_record(
                build_input=RecordBuildInput(
                    evalCaseId="case_002",
                    taskId="task_002_old",
                    taskStatus=TaskStatus.COMPLETED,
                    resultStatus=ResultStatus.AVAILABLE,
                    durationMs=200,
                    schemaValid=True,
                ),
                prompt_metadata=PROMPT_METADATA,
                provider_id="provider-local",
                model_id="model-local",
            ),
        ),
    )

    comparison = build_report_comparison(current_records=records, baseline=baseline)
    report = build_report(
        report_id="report_001",
        report_type=EvalReportType.BASELINE_COMPARISON,
        records=records,
        prompt_metadata=PROMPT_METADATA,
        provider_id="provider-local",
        model_id="model-local",
        created_at="2026-03-26T00:00:00Z",
        comparison=comparison,
    )

    assert comparison.baselineId == "baseline_v1"
    assert comparison.changedCaseIds == ("case_002",)
    assert comparison.availableDelta == -1
    assert comparison.blockedDelta == 1
    assert report.reportType is EvalReportType.BASELINE_COMPARISON


def test_build_report_comparison_rejects_missing_current_record() -> None:
    baseline = build_baseline(
        baseline_id="baseline_v1",
        cases=(
            build_eval_case(
                dataset_entry=build_dataset_entry(case_id="case_001", included_in_baseline=True),
                dataset_ref="datasets/scoring/case_001.json",
                goal="case 1",
            ),
            build_eval_case(
                dataset_entry=build_dataset_entry(case_id="case_002", included_in_baseline=True),
                dataset_ref="datasets/scoring/case_002.json",
                goal="case 2",
            ),
        ),
        prompt_metadata=PROMPT_METADATA,
        provider_id="provider-local",
        model_id="model-local",
        created_at="2026-03-25T00:00:00Z",
        records=(
            build_eval_record(
                build_input=RecordBuildInput(
                    evalCaseId="case_001",
                    taskId="task_001_old",
                    taskStatus=TaskStatus.COMPLETED,
                    resultStatus=ResultStatus.AVAILABLE,
                    durationMs=100,
                    schemaValid=True,
                ),
                prompt_metadata=PROMPT_METADATA,
                provider_id="provider-local",
                model_id="model-local",
            ),
            build_eval_record(
                build_input=RecordBuildInput(
                    evalCaseId="case_002",
                    taskId="task_002_old",
                    taskStatus=TaskStatus.COMPLETED,
                    resultStatus=ResultStatus.AVAILABLE,
                    durationMs=200,
                    schemaValid=True,
                ),
                prompt_metadata=PROMPT_METADATA,
                provider_id="provider-local",
                model_id="model-local",
            ),
        ),
    )

    with pytest.raises(EvalBuildError, match="缺少 baseline case"):
        build_report_comparison(
            current_records=(
                build_eval_record(
                    build_input=RecordBuildInput(
                        evalCaseId="case_001",
                        taskId="task_001",
                        taskStatus=TaskStatus.COMPLETED,
                        resultStatus=ResultStatus.AVAILABLE,
                        durationMs=100,
                        schemaValid=True,
                    ),
                    prompt_metadata=PROMPT_METADATA,
                    provider_id="provider-local",
                    model_id="model-local",
                ),
            ),
            baseline=baseline,
        )
