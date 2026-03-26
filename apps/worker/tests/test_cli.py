from __future__ import annotations

import pytest

from worker.cli import main


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
    assert "--dry-run" in captured.out


def test_eval_help_runs(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["eval", "--help"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "--suite" in captured.out
    assert "--dry-run" in captured.out


def test_batch_placeholder_execution_terminates_without_api_handoff(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["batch", "--dry-run", "--source", "evals/smoke.json"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "mode=batch" in captured.out
    assert "status=placeholder" in captured.out
    assert "api_handoff_enabled=False" in captured.out
    assert "real_execution_enabled=False" in captured.out
    assert "no apps/api in-process task handoff" in captured.out


def test_eval_placeholder_execution_terminates_without_api_handoff(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["eval", "--dry-run", "--suite", "smoke"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "mode=eval" in captured.out
    assert "status=placeholder" in captured.out
    assert "api_handoff_enabled=False" in captured.out
    assert "real_execution_enabled=False" in captured.out
    assert "no apps/api in-process task handoff" in captured.out


def test_batch_requires_explicit_dry_run() -> None:
    exit_code = main(["batch"])

    assert exit_code == 2


def test_eval_requires_explicit_dry_run() -> None:
    exit_code = main(["eval"])

    assert exit_code == 2
