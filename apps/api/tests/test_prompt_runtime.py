from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROMPT_RUNTIME_SRC = Path(__file__).resolve().parents[3] / "packages" / "prompt-runtime" / "src"
prompt_runtime_src = str(PROMPT_RUNTIME_SRC)
if prompt_runtime_src not in sys.path:
    sys.path.insert(0, prompt_runtime_src)

from prompt_runtime import (  # noqa: E402
    FilePromptRuntime,
    PromptAssetAmbiguityError,
    PromptAssetInvalidError,
    PromptAssetNotFoundError,
)


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



def build_runtime(prompts_root: Path) -> FilePromptRuntime:
    return FilePromptRuntime(prompts_root=prompts_root)



def test_file_prompt_runtime_returns_frozen_prompt_payload(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="screening-default",
        stage="input_screening",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="screening-default", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-26",
        body="# Screening\n\n请给出输入预检查结果。",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="input_screening",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "screening-default"
    assert resolved.promptVersion == "2026-03-26"
    assert resolved.schemaVersion == "1.0.0"
    assert resolved.rubricVersion == "rubric-v1"
    assert resolved.body == "# Screening\n\n请给出输入预检查结果。"
    assert resolved.__class__.model_config["frozen"] is True



def test_file_prompt_runtime_reads_body_bound_to_selected_prompt_version(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="screening-default", stage="input_screening")
    write_version(
        prompts_root,
        prompt_id="screening-default",
        prompt_version="2026-03-26",
        status="retired",
    )
    write_version(
        prompts_root,
        prompt_id="screening-default",
        prompt_version="2026-03-27",
        status="active",
    )
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-26",
        body="旧版本正文",
    )
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-27",
        body="新版本正文",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="input_screening",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptVersion == "2026-03-27"
    assert resolved.body == "新版本正文"



def test_file_prompt_runtime_filters_by_stage_before_other_scopes(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="screening-generic",
        stage="input_screening",
        input_scope="*",
        evaluation_scope="*",
        provider_scope="*",
        model_scope="*",
    )
    write_version(prompts_root, prompt_id="screening-generic", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-generic",
        prompt_version="2026-03-26",
        body="screening",
    )

    write_registry(
        prompts_root,
        prompt_id="rubric-exact-scopes",
        stage="rubric_evaluation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="rubric-exact-scopes", prompt_version="2026-03-27")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="rubric-exact-scopes",
        prompt_version="2026-03-27",
        body="rubric",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="input_screening",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "screening-generic"
    assert resolved.body == "screening"



def test_file_prompt_runtime_excludes_registry_records_with_unloadable_status(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="rubric-retired-exact",
        stage="rubric_evaluation",
        status="retired",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="rubric-retired-exact", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="rubric-retired-exact",
        prompt_version="2026-03-26",
        body="retired exact",
    )

    write_registry(
        prompts_root,
        prompt_id="rubric-active-fallback",
        stage="rubric_evaluation",
        status="active",
        input_scope="*",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="rubric-active-fallback", prompt_version="2026-03-27")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="rubric-active-fallback",
        prompt_version="2026-03-27",
        body="active fallback",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="rubric_evaluation",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "rubric-active-fallback"
    assert resolved.body == "active fallback"



def test_file_prompt_runtime_prefers_active_registry_status_after_scope_tie(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="rubric-candidate-exact",
        stage="rubric_evaluation",
        status="candidate",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="rubric-candidate-exact", prompt_version="2026-03-26", status="active")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="rubric-candidate-exact",
        prompt_version="2026-03-26",
        body="candidate exact",
    )

    write_registry(
        prompts_root,
        prompt_id="rubric-active-exact",
        stage="rubric_evaluation",
        status="active",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="rubric-active-exact", prompt_version="2026-03-27", status="active")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="rubric-active-exact",
        prompt_version="2026-03-27",
        body="active exact",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="rubric_evaluation",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "rubric-active-exact"
    assert resolved.body == "active exact"



def test_file_prompt_runtime_falls_back_to_candidate_when_active_does_not_match_scope(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="rubric-active-other-provider",
        stage="rubric_evaluation",
        status="active",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-other",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="rubric-active-other-provider", prompt_version="2026-03-26", status="active")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="rubric-active-other-provider",
        prompt_version="2026-03-26",
        body="active other provider",
    )

    write_registry(
        prompts_root,
        prompt_id="rubric-candidate-fallback",
        stage="rubric_evaluation",
        status="candidate",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="*",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="rubric-candidate-fallback", prompt_version="2026-03-27", status="active")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="rubric-candidate-fallback",
        prompt_version="2026-03-27",
        body="candidate fallback",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="rubric_evaluation",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "rubric-candidate-fallback"
    assert resolved.body == "candidate fallback"



def test_file_prompt_runtime_prefers_input_scope_before_later_scopes(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="prompt-input-exact",
        stage="rubric_evaluation",
        input_scope="chapters_outline",
        evaluation_scope="*",
        provider_scope="*",
        model_scope="*",
    )
    write_version(prompts_root, prompt_id="prompt-input-exact", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="prompt-input-exact",
        prompt_version="2026-03-26",
        body="input exact",
    )

    write_registry(
        prompts_root,
        prompt_id="prompt-eval-exact",
        stage="rubric_evaluation",
        input_scope="*",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="prompt-eval-exact", prompt_version="2026-03-27")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="prompt-eval-exact",
        prompt_version="2026-03-27",
        body="eval exact",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="rubric_evaluation",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "prompt-input-exact"
    assert resolved.body == "input exact"



def test_file_prompt_runtime_prefers_evaluation_scope_before_provider_and_model(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="prompt-eval-exact",
        stage="rubric_evaluation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="*",
        model_scope="*",
    )
    write_version(prompts_root, prompt_id="prompt-eval-exact", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="prompt-eval-exact",
        prompt_version="2026-03-26",
        body="eval exact",
    )

    write_registry(
        prompts_root,
        prompt_id="prompt-provider-model-exact",
        stage="rubric_evaluation",
        input_scope="chapters_outline",
        evaluation_scope="*",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="prompt-provider-model-exact", prompt_version="2026-03-27")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="prompt-provider-model-exact",
        prompt_version="2026-03-27",
        body="provider model exact",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="rubric_evaluation",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "prompt-eval-exact"
    assert resolved.body == "eval exact"



def test_file_prompt_runtime_prefers_provider_scope_before_model_scope(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="prompt-provider-exact",
        stage="aggregation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="*",
    )
    write_version(prompts_root, prompt_id="prompt-provider-exact", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="aggregation",
        prompt_id="prompt-provider-exact",
        prompt_version="2026-03-26",
        body="provider exact",
    )

    write_registry(
        prompts_root,
        prompt_id="prompt-model-exact",
        stage="aggregation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="*",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="prompt-model-exact", prompt_version="2026-03-27")
    write_body(
        prompts_root,
        stage_directory="aggregation",
        prompt_id="prompt-model-exact",
        prompt_version="2026-03-27",
        body="model exact",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="aggregation",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "prompt-provider-exact"
    assert resolved.body == "provider exact"



def test_file_prompt_runtime_prefers_enabled_only_after_scope_tie(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="prompt-disabled",
        stage="aggregation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
        enabled=False,
    )
    write_version(prompts_root, prompt_id="prompt-disabled", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="aggregation",
        prompt_id="prompt-disabled",
        prompt_version="2026-03-26",
        body="disabled",
    )

    write_registry(
        prompts_root,
        prompt_id="prompt-enabled",
        stage="aggregation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
        enabled=True,
    )
    write_version(prompts_root, prompt_id="prompt-enabled", prompt_version="2026-03-27")
    write_body(
        prompts_root,
        stage_directory="aggregation",
        prompt_id="prompt-enabled",
        prompt_version="2026-03-27",
        body="enabled",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="aggregation",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptId == "prompt-enabled"
    assert resolved.body == "enabled"



def test_file_prompt_runtime_fails_when_best_ranked_candidate_is_disabled(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="prompt-disabled-best",
        stage="aggregation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
        enabled=False,
    )
    write_version(prompts_root, prompt_id="prompt-disabled-best", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="aggregation",
        prompt_id="prompt-disabled-best",
        prompt_version="2026-03-26",
        body="disabled best",
    )

    write_registry(
        prompts_root,
        prompt_id="prompt-enabled-generic",
        stage="aggregation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="*",
        enabled=True,
    )
    write_version(prompts_root, prompt_id="prompt-enabled-generic", prompt_version="2026-03-27")
    write_body(
        prompts_root,
        stage_directory="aggregation",
        prompt_id="prompt-enabled-generic",
        prompt_version="2026-03-27",
        body="enabled generic",
    )

    with pytest.raises(PromptAssetNotFoundError, match="enabled"):
        build_runtime(prompts_root).resolve(
            stage="aggregation",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )



def test_file_prompt_runtime_fails_when_selected_version_metadata_is_missing(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="screening-default", stage="input_screening")
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-26",
        body="body",
    )

    with pytest.raises(PromptAssetNotFoundError, match="version"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )



def test_file_prompt_runtime_fails_when_selected_body_is_missing(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="screening-default", stage="input_screening")
    write_version(prompts_root, prompt_id="screening-default", prompt_version="2026-03-26")

    with pytest.raises(PromptAssetNotFoundError, match="Markdown"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )



def test_file_prompt_runtime_fails_when_multiple_best_candidates_remain(prompts_root: Path) -> None:
    write_registry(
        prompts_root,
        prompt_id="prompt-one",
        stage="rubric_evaluation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="prompt-one", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="prompt-one",
        prompt_version="2026-03-26",
        body="one",
    )

    write_registry(
        prompts_root,
        prompt_id="prompt-two",
        stage="rubric_evaluation",
        input_scope="chapters_outline",
        evaluation_scope="full",
        provider_scope="provider-local",
        model_scope="model-local",
    )
    write_version(prompts_root, prompt_id="prompt-two", prompt_version="2026-03-27")
    write_body(
        prompts_root,
        stage_directory="rubric",
        prompt_id="prompt-two",
        prompt_version="2026-03-27",
        body="two",
    )

    with pytest.raises(PromptAssetAmbiguityError, match="prompt-one"):
        build_runtime(prompts_root).resolve(
            stage="rubric_evaluation",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )



def test_file_prompt_runtime_prefers_active_version_over_candidate_version(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="screening-default", stage="input_screening")
    write_version(prompts_root, prompt_id="screening-default", prompt_version="2026-03-26", status="active")
    write_version(prompts_root, prompt_id="screening-default", prompt_version="2026-03-27", status="candidate")
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-26",
        body="body active",
    )
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-27",
        body="body candidate",
    )

    resolved = build_runtime(prompts_root).resolve(
        stage="input_screening",
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-local",
        model_id="model-local",
    )

    assert resolved.promptVersion == "2026-03-26"
    assert resolved.body == "body active"



def test_file_prompt_runtime_rejects_prompt_id_that_breaks_asset_boundaries(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id=".", stage="input_screening")
    write_version(prompts_root, prompt_id=".", prompt_version="2026-03-26", status="active")
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id=".",
        prompt_version="2026-03-26",
        body="boundary break",
    )

    with pytest.raises(PromptAssetInvalidError, match="promptId"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )



def test_file_prompt_runtime_rejects_prompt_id_with_windows_trailing_dot_alias(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="alias.", stage="input_screening")
    write_version(prompts_root, prompt_id="alias.", prompt_version="2026-03-26", status="active")
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="alias.",
        prompt_version="2026-03-26",
        body="alias body",
    )

    with pytest.raises(PromptAssetInvalidError, match="promptId"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


REPO_PROMPTS_ROOT = Path(__file__).resolve().parents[3] / "prompts"
REPO_PROMPT_CASES = (
    pytest.param("input_screening", "screening", "screening-default", id="repo-screening"),
    pytest.param("rubric_evaluation", "rubric", "rubric-default", id="repo-rubric"),
    pytest.param("aggregation", "aggregation", "aggregation-default", id="repo-aggregation"),
)


@pytest.mark.parametrize(("stage", "stage_directory", "prompt_id"), REPO_PROMPT_CASES)
def test_file_prompt_runtime_resolves_repository_prompt_assets(
    stage: str,
    stage_directory: str,
    prompt_id: str,
) -> None:
    resolved = FilePromptRuntime(prompts_root=REPO_PROMPTS_ROOT).resolve(
        stage=stage,
        input_composition="chapters_outline",
        evaluation_mode="full",
        provider_id="provider-deepseek",
        model_id="deepseek-chat",
    )

    body_path = REPO_PROMPTS_ROOT / "scoring" / stage_directory / prompt_id / "v1.md"

    assert resolved.promptId == prompt_id
    assert resolved.promptVersion == "v1"
    assert resolved.schemaVersion == "1.0.0"
    assert resolved.rubricVersion == "rubric-v1"
    assert resolved.body == body_path.read_text(encoding="utf-8")
    assert resolved.body.strip()
