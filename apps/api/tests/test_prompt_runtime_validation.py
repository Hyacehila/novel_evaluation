from __future__ import annotations

from pathlib import Path

import pytest

from prompt_runtime import PromptAssetInvalidError

from .conftest import (
    build_runtime,
    write_body,
    write_registry,
    write_registry_yaml,
    write_version,
    write_version_yaml,
)


def test_file_prompt_runtime_fails_when_selected_body_is_blank(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="screening-default", stage="input_screening")
    write_version(prompts_root, prompt_id="screening-default", prompt_version="2026-03-26")
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-26",
        body="\n  \n",
    )

    with pytest.raises(PromptAssetInvalidError, match="Markdown 正文为空"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_nested_registry_yaml_structure(prompts_root: Path) -> None:
    write_registry_yaml(
        prompts_root,
        file_name="screening-default.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "stage: input_screening",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
                "enabled: true",
                "notes:",
                "  detail: nested-value",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="仅支持顶层 key: value YAML"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_yaml_line_without_key_value_separator(prompts_root: Path) -> None:
    write_registry_yaml(
        prompts_root,
        file_name="screening-default.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "stage: input_screening",
                "status active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
                "enabled: true",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="仅支持顶层 key: value YAML"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_registry_yaml_with_duplicate_keys(prompts_root: Path) -> None:
    write_registry_yaml(
        prompts_root,
        file_name="screening-default.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "promptId: screening-duplicate",
                "stage: input_screening",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
                "enabled: true",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="YAML key 重复"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_registry_yaml_missing_required_fields(prompts_root: Path) -> None:
    write_registry_yaml(
        prompts_root,
        file_name="screening-default.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "stage: input_screening",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="YAML 缺少必填字段"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_version_yaml_missing_required_fields(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="screening-default", stage="input_screening")
    write_version_yaml(
        prompts_root,
        prompt_id="screening-default",
        file_name="2026-03-26.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "promptVersion: 2026-03-26",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "owner: runtime-tests",
                "updatedAt: 2026-03-26T00:00:00Z",
                "changeSummary: initial version",
                "rollbackTarget: previous-stable",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="YAML 缺少必填字段"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_prompt_version_with_path_traversal_segment(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="screening-default", stage="input_screening")
    write_version_yaml(
        prompts_root,
        prompt_id="screening-default",
        file_name="2026-03-26.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "promptVersion: ../escape",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "owner: runtime-tests",
                "updatedAt: 2026-03-26T00:00:00Z",
                "changeSummary: initial version",
                "rollbackTarget: previous-stable",
                "evalRequirement: controlled-regression",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="promptVersion"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_registry_file_name_mismatched_with_prompt_id(prompts_root: Path) -> None:
    write_registry_yaml(
        prompts_root,
        file_name="screening-default.yaml",
        content="\n".join(
            [
                "promptId: screening-other",
                "stage: input_screening",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
                "enabled: true",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="promptId"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_version_file_name_mismatched_with_prompt_version(prompts_root: Path) -> None:
    write_registry(prompts_root, prompt_id="screening-default", stage="input_screening")
    write_version_yaml(
        prompts_root,
        prompt_id="screening-default",
        file_name="2026-03-26.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "promptVersion: 2026-03-27",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "owner: runtime-tests",
                "updatedAt: 2026-03-26T00:00:00Z",
                "changeSummary: initial version",
                "rollbackTarget: previous-stable",
                "evalRequirement: controlled-regression",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="promptVersion"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_fails_when_selected_active_version_has_schema_mismatch_instead_of_falling_back(
    prompts_root: Path,
) -> None:
    write_registry(
        prompts_root,
        prompt_id="screening-default",
        stage="input_screening",
        schema_version="1.0.0",
    )
    write_version(
        prompts_root,
        prompt_id="screening-default",
        prompt_version="2026-03-26",
        schema_version="2.0.0",
        status="active",
    )
    write_version(
        prompts_root,
        prompt_id="screening-default",
        prompt_version="2026-03-27",
        schema_version="1.0.0",
        status="candidate",
    )
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-26",
        body="broken active",
    )
    write_body(
        prompts_root,
        stage_directory="screening",
        prompt_id="screening-default",
        prompt_version="2026-03-27",
        body="candidate fallback",
    )

    with pytest.raises(PromptAssetInvalidError, match="schemaVersion 不一致"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_registry_yaml_with_invalid_stage(prompts_root: Path) -> None:
    write_registry_yaml(
        prompts_root,
        file_name="screening-default.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "stage: invalid-stage",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
                "enabled: true",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="registry 元数据非法"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_registry_yaml_with_invalid_status(prompts_root: Path) -> None:
    write_registry_yaml(
        prompts_root,
        file_name="screening-default.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "stage: input_screening",
                "status: enabled",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
                "enabled: true",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="registry 元数据非法"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )


def test_file_prompt_runtime_rejects_registry_yaml_with_non_boolean_enabled(prompts_root: Path) -> None:
    write_registry_yaml(
        prompts_root,
        file_name="screening-default.yaml",
        content="\n".join(
            [
                "promptId: screening-default",
                "stage: input_screening",
                "status: active",
                "schemaVersion: 1.0.0",
                "rubricVersion: rubric-v1",
                "inputCompositionScope: chapters_outline",
                "evaluationModeScope: full",
                "providerScope: provider-local",
                "modelScope: model-local",
                "enabled: yes",
            ]
        ),
    )

    with pytest.raises(PromptAssetInvalidError, match="registry 元数据非法"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )
