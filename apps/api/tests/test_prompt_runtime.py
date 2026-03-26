from __future__ import annotations

from pathlib import Path

import pytest

from prompt_runtime import (
    PromptAssetAmbiguityError,
    PromptAssetInvalidError,
    PromptAssetNotFoundError,
)

from .conftest import build_runtime, write_body, write_registry, write_version



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
