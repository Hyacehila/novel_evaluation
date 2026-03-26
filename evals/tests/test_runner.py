from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.schemas.common.enums import ResultStatus
from packages.schemas.evals import EvalReportType
from packages.schemas.output.error import ErrorCode

from evals.builders import EvalBuildError
from evals.runners.minimal_runner import MinimalEvalRunner, MinimalRunnerCase, MinimalRunnerResult
from evals.writers import EvalPathError


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture
def runner_fixture(tmp_path: Path) -> tuple[MinimalEvalRunner, Path]:
    evals_root = tmp_path / "evals"
    prompts_root = tmp_path / "prompts"
    (prompts_root / "registry").mkdir(parents=True)
    (prompts_root / "versions" / "screening-default").mkdir(parents=True)
    (prompts_root / "registry" / "screening-default.yaml").write_text(
        "\n".join(
            [
                "promptId: screening-default",
                "stage: input_screening",
                "status: candidate",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
                "enabled: true",
            ]
        ),
        encoding="utf-8",
    )
    (prompts_root / "versions" / "screening-default" / "v1.yaml").write_text(
        "\n".join(
            [
                "promptId: screening-default",
                "promptVersion: v1",
                "status: candidate",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "owner: tests",
                "updatedAt: 2026-03-26T00:00:00Z",
                "changeSummary: initial",
                "rollbackTarget: none",
                "evalRequirement: focused",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        evals_root / "datasets" / "scoring" / "case_001.json",
        {
            "caseId": "case_001",
            "title": "样本 1",
            "inputComposition": "chapters_outline",
            "chaptersRef": "datasets/fixtures/case_001-chapters.md",
            "outlineRef": "datasets/fixtures/case_001-outline.md",
            "expectedOutcomeType": "available",
            "includedInBaseline": True,
            "notes": "最小样本",
        },
    )
    write_json(
        evals_root / "datasets" / "scoring" / "case_002.json",
        {
            "caseId": "case_002",
            "title": "样本 2",
            "inputComposition": "chapters_outline",
            "chaptersRef": "datasets/fixtures/case_002-chapters.md",
            "outlineRef": "datasets/fixtures/case_002-outline.md",
            "expectedOutcomeType": "blocked",
            "includedInBaseline": True,
            "notes": "阻断样本",
        },
    )
    runner = MinimalEvalRunner(evals_root=evals_root, prompts_root=prompts_root)
    return runner, evals_root


def test_minimal_runner_builds_records_and_summary_report(runner_fixture: tuple[MinimalEvalRunner, Path]) -> None:
    runner, _ = runner_fixture

    outcome = runner.run(
        cases=(
            MinimalRunnerCase(
                dataset_ref="datasets/scoring/case_001.json",
                goal="case 1",
                result=MinimalRunnerResult.available(task_id="task_001", duration_ms=100),
            ),
            MinimalRunnerCase(
                dataset_ref="datasets/scoring/case_002.json",
                goal="case 2",
                result=MinimalRunnerResult.blocked(
                    task_id="task_002",
                    duration_ms=200,
                    error_code=ErrorCode.RESULT_BLOCKED,
                    error_message="业务阻断",
                ),
            ),
        ),
        prompt_id="screening-default",
        prompt_version="v1",
        provider_id="provider-local",
        model_id="model-local",
        report_id="report_001",
        created_at="2026-03-26T00:00:00Z",
    )

    assert len(outcome.records) == 2
    assert outcome.records[0].resultStatus is ResultStatus.AVAILABLE
    assert outcome.records[1].resultStatus is ResultStatus.BLOCKED
    assert outcome.report.reportType is EvalReportType.EXECUTION_SUMMARY
    assert outcome.report.summary.availableCount == 1
    assert outcome.report.summary.blockedCount == 1


def test_minimal_runner_generates_baseline_and_comparison_report(runner_fixture: tuple[MinimalEvalRunner, Path]) -> None:
    runner, evals_root = runner_fixture
    baseline_outcome = runner.run(
        cases=(
            MinimalRunnerCase(
                dataset_ref="datasets/scoring/case_001.json",
                goal="case 1",
                result=MinimalRunnerResult.available(task_id="task_001", duration_ms=100),
            ),
            MinimalRunnerCase(
                dataset_ref="datasets/scoring/case_002.json",
                goal="case 2",
                result=MinimalRunnerResult.available(task_id="task_002", duration_ms=200),
            ),
        ),
        prompt_id="screening-default",
        prompt_version="v1",
        provider_id="provider-local",
        model_id="model-local",
        report_id="report_baseline",
        baseline_id="baseline_v1",
        created_at="2026-03-25T00:00:00Z",
    )
    runner.write_outputs(baseline_outcome)

    outcome = runner.run(
        cases=(
            MinimalRunnerCase(
                dataset_ref="datasets/scoring/case_001.json",
                goal="case 1",
                result=MinimalRunnerResult.available(task_id="task_003", duration_ms=100),
            ),
            MinimalRunnerCase(
                dataset_ref="datasets/scoring/case_002.json",
                goal="case 2",
                result=MinimalRunnerResult.blocked(
                    task_id="task_004",
                    duration_ms=200,
                    error_code=ErrorCode.RESULT_BLOCKED,
                    error_message="业务阻断",
                ),
            ),
        ),
        prompt_id="screening-default",
        prompt_version="v1",
        provider_id="provider-local",
        model_id="model-local",
        report_id="report_001",
        baseline_id="baseline_v1",
        created_at="2026-03-26T00:00:00Z",
    )
    baseline_path, report_path = runner.write_outputs(outcome)

    assert outcome.baseline is not None
    assert outcome.should_persist_baseline is False
    assert outcome.report.reportType is EvalReportType.BASELINE_COMPARISON
    assert outcome.report.comparison is not None
    assert outcome.report.comparison.changedCaseIds == ("case_002",)
    assert baseline_path is None
    assert report_path.exists()
    assert (evals_root / "baselines" / "baseline_v1.json").exists()


def test_minimal_runner_rejects_empty_cases(runner_fixture: tuple[MinimalEvalRunner, Path]) -> None:
    runner, _ = runner_fixture

    with pytest.raises(ValueError, match="至少提供一个 case"):
        runner.run(
            cases=(),
            prompt_id="screening-default",
            prompt_version="v1",
            provider_id="provider-local",
            model_id="model-local",
            report_id="report_001",
            created_at="2026-03-26T00:00:00Z",
        )


def test_minimal_runner_rejects_dataset_path_escape(runner_fixture: tuple[MinimalEvalRunner, Path]) -> None:
    runner, _ = runner_fixture

    with pytest.raises(EvalPathError, match="超出 evals 根目录"):
        runner.run(
            cases=(
                MinimalRunnerCase(
                    dataset_ref="../outside.json",
                    goal="bad case",
                    result=MinimalRunnerResult.available(task_id="task_001", duration_ms=100),
                ),
            ),
            prompt_id="screening-default",
            prompt_version="v1",
            provider_id="provider-local",
            model_id="model-local",
            report_id="report_001",
            created_at="2026-03-26T00:00:00Z",
        )


def test_minimal_runner_rejects_comparison_with_missing_case(runner_fixture: tuple[MinimalEvalRunner, Path]) -> None:
    runner, _ = runner_fixture
    baseline_outcome = runner.run(
        cases=(
            MinimalRunnerCase(
                dataset_ref="datasets/scoring/case_001.json",
                goal="case 1",
                result=MinimalRunnerResult.available(task_id="task_001", duration_ms=100),
            ),
            MinimalRunnerCase(
                dataset_ref="datasets/scoring/case_002.json",
                goal="case 2",
                result=MinimalRunnerResult.available(task_id="task_002", duration_ms=200),
            ),
        ),
        prompt_id="screening-default",
        prompt_version="v1",
        provider_id="provider-local",
        model_id="model-local",
        report_id="report_baseline",
        baseline_id="baseline_v1",
        created_at="2026-03-25T00:00:00Z",
    )
    runner.write_outputs(baseline_outcome)

    with pytest.raises(EvalBuildError, match="缺少 baseline case"):
        runner.run(
            cases=(
                MinimalRunnerCase(
                    dataset_ref="datasets/scoring/case_001.json",
                    goal="case 1",
                    result=MinimalRunnerResult.available(task_id="task_003", duration_ms=100),
                ),
            ),
            prompt_id="screening-default",
            prompt_version="v1",
            provider_id="provider-local",
            model_id="model-local",
            report_id="report_001",
            baseline_id="baseline_v1",
            created_at="2026-03-26T00:00:00Z",
        )
