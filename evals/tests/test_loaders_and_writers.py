from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.schemas.common.enums import InputComposition, ResultStatus, TaskStatus
from packages.schemas.output.error import ErrorCode
from packages.schemas.evals import EvalExpectedOutcomeType

from evals.builders import build_baseline, build_eval_record, build_report
from evals.loaders import load_dataset_entry, load_prompt_metadata_snapshot
from evals.models import EvalDatasetEntry, PromptMetadataSnapshot, RecordBuildInput
from evals.writers import (
    EvalPathError,
    load_baseline,
    load_report,
    write_baseline,
    write_report,
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture
def prompt_metadata() -> PromptMetadataSnapshot:
    return PromptMetadataSnapshot(
        promptId="screening-default",
        promptVersion="v1",
        stage="input_screening",
        schemaVersion="1.0.0",
        rubricVersion="rubric-v1",
        registryStatus="candidate",
        versionStatus="candidate",
        enabled=True,
    )


def test_load_dataset_entry_reads_minimal_dataset_payload(tmp_path: Path) -> None:
    dataset_path = tmp_path / "evals" / "datasets" / "scoring" / "case_001.json"
    dataset_path.parent.mkdir(parents=True)
    write_json(
        dataset_path,
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

    entry = load_dataset_entry(dataset_path)

    assert entry == EvalDatasetEntry(
        caseId="case_001",
        title="样本 1",
        inputComposition=InputComposition.CHAPTERS_OUTLINE,
        chaptersRef="datasets/fixtures/case_001-chapters.md",
        outlineRef="datasets/fixtures/case_001-outline.md",
        expectedOutcomeType=EvalExpectedOutcomeType.AVAILABLE,
        includedInBaseline=True,
        notes="最小样本",
    )


def test_load_prompt_metadata_snapshot_reads_registry_and_version(tmp_path: Path) -> None:
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

    snapshot = load_prompt_metadata_snapshot(prompts_root=prompts_root, prompt_id="screening-default", prompt_version="v1")

    assert snapshot.promptId == "screening-default"
    assert snapshot.promptVersion == "v1"
    assert snapshot.schemaVersion == "1.0.0"
    assert snapshot.enabled is True


def test_baseline_and_report_round_trip(tmp_path: Path, prompt_metadata: PromptMetadataSnapshot) -> None:
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
            prompt_metadata=prompt_metadata,
            provider_id="provider-local",
            model_id="model-local",
        ),
    )
    baseline = build_baseline(
        baseline_id="baseline_v1",
        cases=(),
        prompt_metadata=prompt_metadata,
        provider_id="provider-local",
        model_id="model-local",
        created_at="2026-03-26T00:00:00Z",
        records=records,
        case_ids=("case_001",),
    )
    report = build_report(
        report_id="report_001",
        report_type="execution_summary",
        records=records,
        prompt_metadata=prompt_metadata,
        provider_id="provider-local",
        model_id="model-local",
        created_at="2026-03-26T00:00:00Z",
    )

    baseline_path = write_baseline(root=tmp_path / "evals", baseline=baseline)
    report_path = write_report(root=tmp_path / "evals", report=report)

    assert load_baseline(baseline_path) == baseline
    assert load_report(report_path) == report


def test_write_baseline_rejects_overwrite(tmp_path: Path, prompt_metadata: PromptMetadataSnapshot) -> None:
    records = (
        build_eval_record(
            build_input=RecordBuildInput(
                evalCaseId="case_001",
                taskId="task_001",
                taskStatus=TaskStatus.COMPLETED,
                resultStatus=ResultStatus.BLOCKED,
                errorCode=ErrorCode.RESULT_BLOCKED,
                errorMessage="业务阻断",
                durationMs=100,
                schemaValid=False,
            ),
            prompt_metadata=prompt_metadata,
            provider_id="provider-local",
            model_id="model-local",
        ),
    )
    baseline = build_baseline(
        baseline_id="baseline_v1",
        cases=(),
        prompt_metadata=prompt_metadata,
        provider_id="provider-local",
        model_id="model-local",
        created_at="2026-03-26T00:00:00Z",
        records=records,
        case_ids=("case_001",),
    )
    root = tmp_path / "evals"

    write_baseline(root=root, baseline=baseline)

    with pytest.raises(FileExistsError):
        write_baseline(root=root, baseline=baseline)


def test_writer_rejects_path_outside_evals_root(tmp_path: Path, prompt_metadata: PromptMetadataSnapshot) -> None:
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
            prompt_metadata=prompt_metadata,
            provider_id="provider-local",
            model_id="model-local",
        ),
    )
    report = build_report(
        report_id="report_001",
        report_type="execution_summary",
        records=records,
        prompt_metadata=prompt_metadata,
        provider_id="provider-local",
        model_id="model-local",
        created_at="2026-03-26T00:00:00Z",
    )

    with pytest.raises(EvalPathError):
        write_report(root=tmp_path / "other-root", report=report)
