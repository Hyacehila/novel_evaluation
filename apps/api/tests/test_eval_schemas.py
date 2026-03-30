from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.schemas.common.enums import InputComposition, ResultStatus, TaskStatus
from packages.schemas.evals import (
    EvalBaseline,
    EvalBaselineComparison,
    EvalCase,
    EvalExecutionSummary,
    EvalExpectedOutcomeType,
    EvalRecord,
    EvalReport,
    EvalReportType,
)
from packages.schemas.output.error import ErrorCode
from packages.schemas.common.enums import AxisId, ScoreBand
from packages.schemas.output.result import EvaluationResult


def build_result() -> EvaluationResult:
    return EvaluationResult(
        taskId="task_eval_1",
        schemaVersion="1.0.0",
        promptVersion="prompt-v1",
        rubricVersion="rubric-v1",
        providerId="provider-local",
        modelId="model-local",
        resultTime="2026-03-25T00:00:00Z",
        axes=[
            {
                "axisId": axis_id.value,
                "scoreBand": ScoreBand.THREE.value,
                "score": 75,
                "summary": f"{axis_id.value} 维度总结",
                "reason": "证据充分，表现合格。",
                "degradedByInput": False,
                "riskTags": [],
            }
            for axis_id in AxisId
        ],
        overall={
            "score": 80,
            "verdict": "可继续观察",
            "verdictSubQuote": "当前样本已体现基础市场承接力，但仍需观察长线兑现稳定性。",
            "summary": "整体完成度稳定。",
            "platformCandidates": [{"name": "女频平台 A", "weight": 100, "pitchQuote": "情感走向与平台核心读者预期一致，具备明确承接空间。"}],
            "marketFit": "具备一定市场接受度",
            "strengths": ["结构完成度稳定"],
            "weaknesses": ["长线兑现仍需继续观察"],
        },
    )


def build_summary(total: int = 2) -> EvalExecutionSummary:
    return EvalExecutionSummary(
        totalCount=total,
        availableCount=1,
        blockedCount=1 if total > 1 else 0,
        failedCount=0,
        schemaValidCount=1,
    )


def test_eval_case_accepts_minimal_payload() -> None:
    case = EvalCase(
        caseId="case_001",
        datasetRef="datasets/scoring/case_001.json",
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        goal="验证双侧强输入时可产出正式结果",
        expectedOutcomeType=EvalExpectedOutcomeType.AVAILABLE,
        includedInBaseline=True,
    )

    assert case.caseId == "case_001"
    assert case.expectedOutcomeType is EvalExpectedOutcomeType.AVAILABLE


def test_eval_case_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        EvalCase(
            caseId="case_001",
            datasetRef="datasets/scoring/case_001.json",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            goal="验证双侧强输入时可产出正式结果",
            expectedOutcomeType=EvalExpectedOutcomeType.AVAILABLE,
            includedInBaseline=True,
            extraField="forbidden",
        )


def test_eval_case_is_frozen() -> None:
    case = EvalCase(
        caseId="case_001",
        datasetRef="datasets/scoring/case_001.json",
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        goal="验证双侧强输入时可产出正式结果",
        expectedOutcomeType=EvalExpectedOutcomeType.AVAILABLE,
        includedInBaseline=True,
    )

    with pytest.raises(ValidationError):
        case.goal = "新的目标"


def test_eval_record_accepts_available_result() -> None:
    record = EvalRecord(
        evalCaseId="case_001",
        taskId="task_eval_1",
        schemaVersion="1.0.0",
        promptVersion="prompt-v1",
        rubricVersion="rubric-v1",
        providerId="provider-local",
        modelId="model-local",
        taskStatus=TaskStatus.COMPLETED,
        resultStatus=ResultStatus.AVAILABLE,
        durationMs=3200,
        schemaValid=True,
    )

    assert record.resultStatus is ResultStatus.AVAILABLE


def test_eval_record_available_requires_schema_valid() -> None:
    with pytest.raises(ValidationError):
        EvalRecord(
            evalCaseId="case_001",
            taskId="task_eval_1",
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            taskStatus=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.AVAILABLE,
            durationMs=3200,
            schemaValid=False,
        )


def test_eval_record_available_rejects_error_semantics() -> None:
    with pytest.raises(ValidationError):
        EvalRecord(
            evalCaseId="case_001",
            taskId="task_eval_1",
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            taskStatus=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.AVAILABLE,
            errorCode=ErrorCode.RESULT_BLOCKED,
            errorMessage="不应存在",
            durationMs=3200,
            schemaValid=True,
        )


def test_eval_record_rejects_non_terminal_status_combination() -> None:
    with pytest.raises(ValidationError):
        EvalRecord(
            evalCaseId="case_001",
            taskId="task_eval_1",
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            taskStatus=TaskStatus.PROCESSING,
            resultStatus=ResultStatus.NOT_AVAILABLE,
            durationMs=3200,
            schemaValid=False,
        )


def test_eval_record_requires_blocked_error_code() -> None:
    with pytest.raises(ValidationError):
        EvalRecord(
            evalCaseId="case_002",
            taskId="task_eval_2",
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            taskStatus=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.BLOCKED,
            errorCode=ErrorCode.INTERNAL_ERROR,
            errorMessage="错误分类不匹配",
            durationMs=1200,
            schemaValid=False,
        )


def test_eval_record_blocked_rejects_schema_valid_true() -> None:
    with pytest.raises(ValidationError):
        EvalRecord(
            evalCaseId="case_002",
            taskId="task_eval_2",
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            taskStatus=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.BLOCKED,
            errorCode=ErrorCode.RESULT_BLOCKED,
            errorMessage="业务阻断",
            durationMs=1200,
            schemaValid=True,
        )


def test_eval_record_blocked_requires_error_semantics() -> None:
    with pytest.raises(ValidationError):
        EvalRecord(
            evalCaseId="case_002",
            taskId="task_eval_2",
            schemaVersion="1.0.0",
            promptVersion="prompt-v1",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            taskStatus=TaskStatus.COMPLETED,
            resultStatus=ResultStatus.BLOCKED,
            durationMs=1200,
            schemaValid=False,
        )


def test_eval_record_accepts_failed_not_available_state() -> None:
    record = EvalRecord(
        evalCaseId="case_003",
        taskId="task_eval_3",
        schemaVersion="1.0.0",
        promptVersion="prompt-v1",
        rubricVersion="rubric-v1",
        providerId="provider-local",
        modelId="model-local",
        taskStatus=TaskStatus.FAILED,
        resultStatus=ResultStatus.NOT_AVAILABLE,
        errorCode=ErrorCode.TIMEOUT,
        errorMessage="调用超时",
        durationMs=5000,
        schemaValid=False,
    )

    assert record.errorCode is ErrorCode.TIMEOUT


def test_eval_baseline_validates_summary_alignment() -> None:
    with pytest.raises(ValidationError):
        EvalBaseline(
            baselineId="baseline_v1",
            caseIds=("case_001", "case_002"),
            promptVersion="prompt-v1",
            schemaVersion="1.0.0",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            createdAt="2026-03-25T00:00:00Z",
            summary=EvalExecutionSummary(
                totalCount=1,
                availableCount=1,
                blockedCount=0,
                failedCount=0,
                schemaValidCount=1,
            ),
        )


def test_eval_baseline_accepts_valid_payload() -> None:
    baseline = EvalBaseline(
        baselineId="baseline_v1",
        caseIds=("case_001", "case_002"),
        promptVersion="prompt-v1",
        schemaVersion="1.0.0",
        rubricVersion="rubric-v1",
        providerId="provider-local",
        modelId="model-local",
        createdAt="2026-03-25T00:00:00Z",
        summary=build_summary(),
    )

    assert baseline.summary.totalCount == 2


def test_eval_baseline_rejects_duplicate_case_ids() -> None:
    with pytest.raises(ValidationError):
        EvalBaseline(
            baselineId="baseline_v1",
            caseIds=("case_001", "case_001"),
            promptVersion="prompt-v1",
            schemaVersion="1.0.0",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            createdAt="2026-03-25T00:00:00Z",
            summary=EvalExecutionSummary(
                totalCount=2,
                availableCount=1,
                blockedCount=1,
                failedCount=0,
                schemaValidCount=1,
            ),
        )


def test_eval_execution_summary_rejects_schema_valid_count_above_available() -> None:
    with pytest.raises(ValidationError):
        EvalExecutionSummary(
            totalCount=2,
            availableCount=1,
            blockedCount=1,
            failedCount=0,
            schemaValidCount=2,
        )


def test_eval_report_requires_comparison_for_baseline_comparison_type() -> None:
    with pytest.raises(ValidationError):
        EvalReport(
            reportId="report_001",
            reportType=EvalReportType.BASELINE_COMPARISON,
            caseIds=("case_001", "case_002"),
            promptVersion="prompt-v1",
            schemaVersion="1.0.0",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            createdAt="2026-03-25T00:00:00Z",
            summary=build_summary(),
        )


def test_eval_report_rejects_comparison_for_execution_summary_type() -> None:
    with pytest.raises(ValidationError):
        EvalReport(
            reportId="report_001",
            reportType=EvalReportType.EXECUTION_SUMMARY,
            caseIds=("case_001", "case_002"),
            promptVersion="prompt-v1",
            schemaVersion="1.0.0",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            createdAt="2026-03-25T00:00:00Z",
            summary=build_summary(),
            comparison=EvalBaselineComparison(
                baselineId="baseline_v1",
                changedCaseIds=("case_002",),
                availableDelta=-1,
                blockedDelta=1,
                failedDelta=0,
                schemaValidDelta=0,
            ),
        )


def test_eval_report_accepts_baseline_comparison_payload() -> None:
    report = EvalReport(
        reportId="report_001",
        reportType=EvalReportType.BASELINE_COMPARISON,
        caseIds=("case_001", "case_002"),
        promptVersion="prompt-v1",
        schemaVersion="1.0.0",
        rubricVersion="rubric-v1",
        providerId="provider-local",
        modelId="model-local",
        createdAt="2026-03-25T00:00:00Z",
        summary=build_summary(),
        comparison=EvalBaselineComparison(
            baselineId="baseline_v1",
            changedCaseIds=("case_002",),
            availableDelta=-1,
            blockedDelta=1,
            failedDelta=0,
            schemaValidDelta=0,
        ),
    )

    assert report.comparison is not None
    assert report.comparison.changedCaseIds == ("case_002",)


def test_eval_report_rejects_changed_case_outside_scope() -> None:
    with pytest.raises(ValidationError):
        EvalReport(
            reportId="report_001",
            reportType=EvalReportType.BASELINE_COMPARISON,
            caseIds=("case_001", "case_002"),
            promptVersion="prompt-v1",
            schemaVersion="1.0.0",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            createdAt="2026-03-25T00:00:00Z",
            summary=build_summary(),
            comparison=EvalBaselineComparison(
                baselineId="baseline_v1",
                changedCaseIds=("case_003",),
                availableDelta=0,
                blockedDelta=0,
                failedDelta=0,
                schemaValidDelta=0,
            ),
        )


def test_eval_report_rejects_delta_without_changed_cases() -> None:
    with pytest.raises(ValidationError):
        EvalReport(
            reportId="report_001",
            reportType=EvalReportType.BASELINE_COMPARISON,
            caseIds=("case_001", "case_002"),
            promptVersion="prompt-v1",
            schemaVersion="1.0.0",
            rubricVersion="rubric-v1",
            providerId="provider-local",
            modelId="model-local",
            createdAt="2026-03-25T00:00:00Z",
            summary=build_summary(),
            comparison=EvalBaselineComparison(
                baselineId="baseline_v1",
                changedCaseIds=(),
                availableDelta=-1,
                blockedDelta=1,
                failedDelta=0,
                schemaValidDelta=0,
            ),
        )


def test_eval_report_rejects_duplicate_changed_case_ids() -> None:
    with pytest.raises(ValidationError):
        EvalBaselineComparison(
            baselineId="baseline_v1",
            changedCaseIds=("case_002", "case_002"),
            availableDelta=-1,
            blockedDelta=1,
            failedDelta=0,
            schemaValidDelta=0,
        )


def test_eval_case_rejects_unsafe_dataset_ref() -> None:
    with pytest.raises(ValidationError):
        EvalCase(
            caseId="case_001",
            datasetRef="../datasets/case_001.json",
            inputComposition=InputComposition.CHAPTERS_OUTLINE,
            goal="验证双侧强输入时可产出正式结果",
            expectedOutcomeType=EvalExpectedOutcomeType.AVAILABLE,
            includedInBaseline=True,
        )


def test_eval_schema_exports_are_importable() -> None:
    assert EvalCase.__name__ == "EvalCase"
    assert EvalRecord.__name__ == "EvalRecord"
    assert EvalBaseline.__name__ == "EvalBaseline"
    assert EvalReport.__name__ == "EvalReport"
    assert EvalReportType.__name__ == "EvalReportType"
