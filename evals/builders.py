from __future__ import annotations

from collections.abc import Iterable

from packages.schemas.common.enums import ResultStatus
from packages.schemas.evals import (
    EvalBaseline,
    EvalBaselineComparison,
    EvalCase,
    EvalExecutionSummary,
    EvalRecord,
    EvalReport,
    EvalReportType,
)

from evals.models import EvalDatasetEntry, PromptMetadataSnapshot, RecordBuildInput


class EvalBuildError(ValueError):
    pass


def build_eval_case(*, dataset_entry: EvalDatasetEntry, dataset_ref: str, goal: str) -> EvalCase:
    return EvalCase(
        caseId=dataset_entry.caseId,
        datasetRef=dataset_ref,
        inputComposition=dataset_entry.inputComposition,
        goal=goal,
        expectedOutcomeType=dataset_entry.expectedOutcomeType,
        includedInBaseline=dataset_entry.includedInBaseline,
    )


def build_eval_record(
    *,
    build_input: RecordBuildInput,
    prompt_metadata: PromptMetadataSnapshot,
    provider_id: str,
    model_id: str,
) -> EvalRecord:
    return EvalRecord(
        evalCaseId=build_input.evalCaseId,
        taskId=build_input.taskId,
        schemaVersion=prompt_metadata.schemaVersion,
        promptVersion=prompt_metadata.promptVersion,
        rubricVersion=prompt_metadata.rubricVersion,
        providerId=provider_id,
        modelId=model_id,
        taskStatus=build_input.taskStatus,
        resultStatus=build_input.resultStatus,
        errorCode=build_input.errorCode,
        errorMessage=build_input.errorMessage,
        durationMs=build_input.durationMs,
        schemaValid=build_input.schemaValid,
    )


def build_execution_summary(records: Iterable[EvalRecord]) -> EvalExecutionSummary:
    record_list = tuple(records)
    available_count = sum(record.resultStatus is ResultStatus.AVAILABLE for record in record_list)
    blocked_count = sum(record.resultStatus is ResultStatus.BLOCKED for record in record_list)
    failed_count = sum(record.resultStatus is ResultStatus.NOT_AVAILABLE for record in record_list)
    schema_valid_count = sum(record.schemaValid for record in record_list)
    return EvalExecutionSummary(
        totalCount=len(record_list),
        availableCount=available_count,
        blockedCount=blocked_count,
        failedCount=failed_count,
        schemaValidCount=schema_valid_count,
    )


def build_baseline(
    *,
    baseline_id: str,
    cases: Iterable[EvalCase],
    prompt_metadata: PromptMetadataSnapshot,
    provider_id: str,
    model_id: str,
    created_at: str,
    records: Iterable[EvalRecord],
    case_ids: tuple[str, ...] | None = None,
) -> EvalBaseline:
    record_list = tuple(records)
    record_map = {record.evalCaseId: record for record in record_list}
    if len(record_map) != len(record_list):
        raise EvalBuildError("baseline records 不允许出现重复 evalCaseId。")

    if case_ids is None:
        ordered_case_ids = tuple(case.caseId for case in cases if case.includedInBaseline)
    else:
        ordered_case_ids = case_ids

    missing_case_ids = tuple(case_id for case_id in ordered_case_ids if case_id not in record_map)
    if missing_case_ids:
        joined_case_ids = ", ".join(missing_case_ids)
        raise EvalBuildError(f"baseline 缺少对应 record：{joined_case_ids}")

    selected_records = tuple(record_map[case_id] for case_id in ordered_case_ids)
    return EvalBaseline(
        baselineId=baseline_id,
        caseIds=ordered_case_ids,
        promptVersion=prompt_metadata.promptVersion,
        schemaVersion=prompt_metadata.schemaVersion,
        rubricVersion=prompt_metadata.rubricVersion,
        providerId=provider_id,
        modelId=model_id,
        createdAt=created_at,
        summary=build_execution_summary(selected_records),
    )


def build_report_comparison(*, current_records: Iterable[EvalRecord], baseline: EvalBaseline) -> EvalBaselineComparison:
    current_record_list = tuple(
        record for record in current_records if record.evalCaseId in set(baseline.caseIds)
    )
    current_record_map = {record.evalCaseId: record for record in current_record_list}
    if len(current_record_map) != len(current_record_list):
        raise EvalBuildError("comparison records 不允许出现重复 evalCaseId。")

    missing_case_ids = tuple(case_id for case_id in baseline.caseIds if case_id not in current_record_map)
    if missing_case_ids:
        joined_case_ids = ", ".join(missing_case_ids)
        raise EvalBuildError(f"comparison 缺少 baseline case 对应 record：{joined_case_ids}")

    current_summary = build_execution_summary(tuple(current_record_map[case_id] for case_id in baseline.caseIds))
    changed_case_ids = tuple(
        case_id
        for case_id in baseline.caseIds
        if current_record_map[case_id].resultStatus is not ResultStatus.AVAILABLE
        or current_record_map[case_id].schemaValid is not True
    )
    return EvalBaselineComparison(
        baselineId=baseline.baselineId,
        changedCaseIds=changed_case_ids,
        availableDelta=current_summary.availableCount - baseline.summary.availableCount,
        blockedDelta=current_summary.blockedCount - baseline.summary.blockedCount,
        failedDelta=current_summary.failedCount - baseline.summary.failedCount,
        schemaValidDelta=current_summary.schemaValidCount - baseline.summary.schemaValidCount,
    )


def build_report(
    *,
    report_id: str,
    report_type: EvalReportType | str,
    records: Iterable[EvalRecord],
    prompt_metadata: PromptMetadataSnapshot,
    provider_id: str,
    model_id: str,
    created_at: str,
    comparison: EvalBaselineComparison | None = None,
) -> EvalReport:
    record_list = tuple(records)
    return EvalReport(
        reportId=report_id,
        reportType=report_type,
        caseIds=tuple(record.evalCaseId for record in record_list),
        promptVersion=prompt_metadata.promptVersion,
        schemaVersion=prompt_metadata.schemaVersion,
        rubricVersion=prompt_metadata.rubricVersion,
        providerId=provider_id,
        modelId=model_id,
        createdAt=created_at,
        summary=build_execution_summary(record_list),
        comparison=comparison,
    )


__all__ = [
    "EvalBuildError",
    "build_baseline",
    "build_eval_case",
    "build_eval_record",
    "build_execution_summary",
    "build_report",
    "build_report_comparison",
]
