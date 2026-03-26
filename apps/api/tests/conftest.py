from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
API_SRC = Path(__file__).resolve().parents[1] / "src"
PROMPT_RUNTIME_SRC = REPO_ROOT / "packages" / "prompt-runtime" / "src"

for path in (REPO_ROOT, API_SRC, PROMPT_RUNTIME_SRC):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from prompt_runtime import FilePromptRuntime  # noqa: E402


@pytest.fixture
def prompts_root(tmp_path: Path) -> Path:
    prompts = tmp_path / "prompts"
    (prompts / "registry").mkdir(parents=True)
    (prompts / "versions").mkdir(parents=True)
    (prompts / "scoring" / "screening").mkdir(parents=True)
    (prompts / "scoring" / "rubric").mkdir(parents=True)
    (prompts / "scoring" / "aggregation").mkdir(parents=True)
    (prompts / "scoring" / "system").mkdir(parents=True)
    (prompts / "scoring" / "templates").mkdir(parents=True)
    return prompts


def write_registry(
    prompts_root: Path,
    *,
    prompt_id: str,
    stage: str,
    schema_version: str = "1.0.0",
    rubric_version: str = "rubric-v1",
    status: str = "active",
    input_scope: str = "*",
    evaluation_scope: str = "*",
    provider_scope: str = "*",
    model_scope: str = "*",
    enabled: bool = True,
) -> None:
    content = "\n".join(
        [
            f"promptId: {prompt_id}",
            f"stage: {stage}",
            f"status: {status}",
            f"schemaVersion: {schema_version}",
            f"rubricVersion: {rubric_version}",
            f"inputCompositionScope: {input_scope}",
            f"evaluationModeScope: {evaluation_scope}",
            f"providerScope: {provider_scope}",
            f"modelScope: {model_scope}",
            f"enabled: {'true' if enabled else 'false'}",
            "notes: test asset",
        ]
    )
    (prompts_root / "registry" / f"{prompt_id}.yaml").write_text(content, encoding="utf-8")


def write_version(
    prompts_root: Path,
    *,
    prompt_id: str,
    prompt_version: str,
    schema_version: str = "1.0.0",
    rubric_version: str = "rubric-v1",
    status: str = "active",
) -> None:
    directory = prompts_root / "versions" / prompt_id
    directory.mkdir(parents=True, exist_ok=True)
    content = "\n".join(
        [
            f"promptId: {prompt_id}",
            f"promptVersion: {prompt_version}",
            f"status: {status}",
            f"schemaVersion: {schema_version}",
            f"rubricVersion: {rubric_version}",
            "owner: runtime-tests",
            "updatedAt: 2026-03-26T00:00:00Z",
            "changeSummary: initial version",
            "rollbackTarget: previous-stable",
            "evalRequirement: controlled-regression",
        ]
    )
    (directory / f"{prompt_version}.yaml").write_text(content, encoding="utf-8")


def write_body(
    prompts_root: Path,
    *,
    stage_directory: str,
    prompt_id: str,
    prompt_version: str,
    body: str,
) -> None:
    directory = prompts_root / "scoring" / stage_directory / prompt_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{prompt_version}.md").write_text(body, encoding="utf-8")


def write_registry_yaml(prompts_root: Path, *, file_name: str, content: str) -> None:
    (prompts_root / "registry" / file_name).write_text(content, encoding="utf-8")


def write_version_yaml(
    prompts_root: Path,
    *,
    prompt_id: str,
    file_name: str,
    content: str,
) -> None:
    directory = prompts_root / "versions" / prompt_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / file_name).write_text(content, encoding="utf-8")


def build_runtime(prompts_root: Path) -> FilePromptRuntime:
    return FilePromptRuntime(prompts_root=prompts_root)
