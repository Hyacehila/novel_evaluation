from __future__ import annotations

from pathlib import Path

import pytest

from prompt_runtime import PromptAssetInvalidError

from .conftest import build_runtime


def test_file_prompt_runtime_rejects_registry_symlink_outside_prompts_root(prompts_root: Path) -> None:
    external_dir = prompts_root.parent / "external-assets"
    external_dir.mkdir()
    external_registry = external_dir / "screening-default.yaml"
    external_registry.write_text(
        "\n".join(
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
            ]
        ),
        encoding="utf-8",
    )
    try:
        (prompts_root / "registry" / "screening-default.yaml").symlink_to(external_registry)
    except OSError as error:
        pytest.skip(f"当前环境不允许创建符号链接: {error}")

    with pytest.raises(PromptAssetInvalidError, match="目录边界"):
        build_runtime(prompts_root).resolve(
            stage="input_screening",
            input_composition="chapters_outline",
            evaluation_mode="full",
            provider_id="provider-local",
            model_id="model-local",
        )
