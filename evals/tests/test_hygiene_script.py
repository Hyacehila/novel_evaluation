from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
HYGIENE_SCRIPT = REPO_ROOT / "scripts" / "repo" / "check-hygiene.ps1"


def _powershell_command() -> str:
    command = shutil.which("pwsh") or shutil.which("powershell")
    if command is None:
        pytest.skip("PowerShell is required for repository hygiene script tests.")
    return command


def _build_minimal_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    script_path = repo_root / "scripts" / "repo" / "check-hygiene.ps1"
    script_path.parent.mkdir(parents=True)
    shutil.copyfile(HYGIENE_SCRIPT, script_path)

    (repo_root / "docs").mkdir()
    (repo_root / "prompts" / "registry").mkdir(parents=True)
    (repo_root / "packages" / "application").mkdir(parents=True)
    (repo_root / "docs" / "runbook.md").write_text("# Runbook\n", encoding="utf-8")
    (repo_root / "README.md").write_text("[Runbook](docs/runbook.md)\n", encoding="utf-8")
    (repo_root / "CONTRIBUTING.md").write_text("[Runbook](docs/runbook.md)\n", encoding="utf-8")
    (repo_root / "CLAUDE.md").write_text("[Runbook](docs/runbook.md)\n", encoding="utf-8")
    (repo_root / ".env.example").write_text("NOVEL_EVAL_DEEPSEEK_API_KEY=\n", encoding="utf-8")
    return repo_root


def _run_hygiene(repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _powershell_command(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo_root / "scripts" / "repo" / "check-hygiene.ps1"),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )


def test_hygiene_script_accepts_current_formal_docs(tmp_path: Path) -> None:
    repo_root = _build_minimal_repo(tmp_path)

    result = _run_hygiene(repo_root)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Repository hygiene check passed." in result.stdout


def test_hygiene_script_rejects_legacy_root_doc_references(tmp_path: Path) -> None:
    repo_root = _build_minimal_repo(tmp_path)
    (repo_root / "CONTRIBUTING.md").write_text(
        "Read docs/operations/local-installation-and-smoke.md\n",
        encoding="utf-8",
    )

    result = _run_hygiene(repo_root)

    assert result.returncode == 1
    assert "Legacy reference 'docs/operations/'" in result.stdout


def test_hygiene_script_rejects_broken_markdown_links(tmp_path: Path) -> None:
    repo_root = _build_minimal_repo(tmp_path)
    (repo_root / "README.md").write_text("[Missing](docs/missing.md)\n", encoding="utf-8")

    result = _run_hygiene(repo_root)

    assert result.returncode == 1
    assert "Broken local Markdown link" in result.stdout


def test_hygiene_script_rejects_legacy_deepseek_model_aliases(tmp_path: Path) -> None:
    repo_root = _build_minimal_repo(tmp_path)
    (repo_root / "prompts" / "registry" / "screening-default.yaml").write_text(
        "modelScope: deepseek-chat\n",
        encoding="utf-8",
    )

    result = _run_hygiene(repo_root)

    assert result.returncode == 1
    assert "Legacy term 'deepseek-chat'" in result.stdout
