from __future__ import annotations

import json
from pathlib import Path

import pytest

import worker  # noqa: F401
from provider_adapters import LocalDeterministicProviderAdapter
from packages.runtime.service_factory import RuntimePromptRuntime
from worker.bootstrap import WorkerRuntimeContext, WorkerRuntimeMetadata, bootstrap_worker_runtime
from worker.cli import main


def _build_context(*, repo_root: Path, evals_root: Path) -> WorkerRuntimeContext:
    prompt_runtime = RuntimePromptRuntime()
    provider_adapter = LocalDeterministicProviderAdapter(
        provider_id="provider-deepseek",
        model_id="deepseek-chat",
        structured_stage_outputs=True,
    )
    return WorkerRuntimeContext(
        command_name="test",
        repo_root=repo_root,
        evals_root=evals_root,
        prompts_root=Path("D:/PythonProject/novel_evaluation/prompts"),
        prompt_runtime=prompt_runtime,
        provider_adapter=provider_adapter,
        runtime_metadata=WorkerRuntimeMetadata(
            schema_version="1.0.0",
            prompt_version="v1",
            rubric_version="rubric-v1",
            provider_id="provider-deepseek",
            model_id="deepseek-chat",
        ),
    )


def _write_json(path: Path, payload: dict[str, object] | list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_eval_fixture(tmp_path: Path) -> tuple[WorkerRuntimeContext, Path]:
    repo_root = tmp_path / "repo"
    evals_root = repo_root / "evals"
    fixtures_root = evals_root / "datasets" / "fixtures"
    fixtures_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        evals_root / "cases" / "smoke.json",
        {
            "suiteId": "smoke",
            "promptId": "screening-default",
            "promptVersion": "v1",
            "cases": [
                {
                    "datasetRef": "datasets/scoring/case_001.json",
                    "goal": "可输出正式结果",
                },
                {
                    "datasetRef": "datasets/scoring/case_002.json",
                    "goal": "跨输入冲突阻断",
                },
            ],
        },
    )
    _write_json(
        evals_root / "datasets" / "scoring" / "case_001.json",
        {
            "caseId": "case_001",
            "title": "成功样本",
            "inputComposition": "chapters_outline",
            "chaptersRef": "datasets/fixtures/case_001_chapters.md",
            "outlineRef": "datasets/fixtures/case_001_outline.md",
            "expectedOutcomeType": "available",
            "includedInBaseline": True,
        },
    )
    _write_json(
        evals_root / "datasets" / "scoring" / "case_002.json",
        {
            "caseId": "case_002",
            "title": "阻断样本",
            "inputComposition": "chapters_outline",
            "chaptersRef": "datasets/fixtures/case_002_chapters.md",
            "outlineRef": "datasets/fixtures/case_002_outline.md",
            "expectedOutcomeType": "blocked",
            "includedInBaseline": True,
        },
    )
    (fixtures_root / "case_001_chapters.md").write_text(
        "修仙宗门危机开局，主角必须在七天内突破。",
        encoding="utf-8",
    )
    (fixtures_root / "case_001_outline.md").write_text(
        "后续主线围绕宗门大比、升级与秘宝展开。",
        encoding="utf-8",
    )
    (fixtures_root / "case_002_chapters.md").write_text(
        "都市豪门婚约开篇，职场与感情冲突同时出现。",
        encoding="utf-8",
    )
    (fixtures_root / "case_002_outline.md").write_text(
        "后续大纲改写为星际机甲远征，题材与前文完全不一致。",
        encoding="utf-8",
    )
    return _build_context(repo_root=repo_root, evals_root=evals_root), evals_root


def test_root_help_lists_batch_and_eval_commands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "batch" in captured.out
    assert "eval" in captured.out


def test_batch_help_runs(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["batch", "--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "--source" in captured.out
    assert "--report-id" in captured.out


def test_eval_help_runs(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["eval", "--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "--suite" in captured.out
    assert "--baseline-id" in captured.out
    assert "--report-id" in captured.out


def test_batch_dry_run_reports_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    context, _ = _build_eval_fixture(tmp_path)
    source_path = tmp_path / "batch.json"
    _write_json(
        source_path,
        [
            {
                "title": "batch sample",
                "chapters": [{"title": "第一章", "content": "修仙危机开篇"}],
                "outline": {"content": "后续主线围绕宗门升级展开"},
                "sourceType": "direct_input",
            }
        ],
    )
    monkeypatch.setattr("worker.cli.bootstrap_worker_runtime", lambda command_name: context)

    exit_code = main(["batch", "--dry-run", "--source", str(source_path)])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "status=dry_run" in captured.out
    assert "real_execution_enabled=True" in captured.out


def test_eval_dry_run_reports_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    context, evals_root = _build_eval_fixture(tmp_path)
    monkeypatch.setattr("worker.cli.bootstrap_worker_runtime", lambda command_name: context)

    exit_code = main(["eval", "--dry-run", "--suite", str(evals_root / "cases" / "smoke.json")])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "status=dry_run" in captured.out
    assert "real_execution_enabled=True" in captured.out


def test_eval_executes_suite_and_writes_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context, evals_root = _build_eval_fixture(tmp_path)
    monkeypatch.setattr("worker.cli.bootstrap_worker_runtime", lambda command_name: context)

    exit_code = main(
        [
            "eval",
            "--suite",
            str(evals_root / "cases" / "smoke.json"),
            "--report-id",
            "report_smoke",
            "--baseline-id",
            "baseline_smoke",
        ]
    )

    assert exit_code == 0
    assert (evals_root / "reports" / "report_smoke.json").exists()
    assert (evals_root / "reports" / "report_smoke.records.json").exists()
    assert (evals_root / "baselines" / "baseline_smoke.json").exists()
    captured = capsys.readouterr()
    assert "status=completed" in captured.out


def test_batch_executes_source_and_writes_summary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context, _ = _build_eval_fixture(tmp_path)
    source_path = tmp_path / "batch.json"
    _write_json(
        source_path,
        [
            {
                "title": "batch success",
                "chapters": [{"title": "第一章", "content": "修仙危机开篇"}],
                "outline": {"content": "后续主线围绕宗门升级展开"},
                "sourceType": "direct_input",
            },
            {
                "title": "batch blocked",
                "chapters": [{"title": "第一章", "content": "都市豪门婚约开篇"}],
                "outline": {"content": "后续切成星际机甲远征"},
                "sourceType": "direct_input",
            },
        ],
    )
    monkeypatch.setattr("worker.cli.bootstrap_worker_runtime", lambda command_name: context)

    exit_code = main(["batch", "--source", str(source_path), "--report-id", "batch_smoke"])

    assert exit_code == 0
    assert (context.repo_root / "output" / "batch" / "batch_smoke.json").exists()
    captured = capsys.readouterr()
    assert "status=completed" in captured.out
    assert "total_count=2" in captured.out


def test_bootstrap_worker_runtime_requires_startup_provider_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVEL_EVAL_DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="NOVEL_EVAL_DEEPSEEK_API_KEY"):
        bootstrap_worker_runtime(command_name="eval")


def test_bootstrap_worker_runtime_uses_startup_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVEL_EVAL_DEEPSEEK_API_KEY", "test-key")

    context = bootstrap_worker_runtime(command_name="eval")

    assert context.runtime_metadata.provider_id == "provider-deepseek"
    assert context.runtime_metadata.model_id == "deepseek-chat"
    assert hasattr(context.provider_adapter, "execute")
