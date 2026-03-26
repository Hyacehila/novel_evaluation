from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from prompt_runtime import (
    PromptAssetInvalidError,
    PromptAssetNotFoundError,
    PromptRegistryRecord,
    PromptVersionRecord,
)

from evals.models import EvalDatasetEntry, PromptMetadataSnapshot


def load_dataset_entry(path: Path | str) -> EvalDatasetEntry:
    dataset_path = Path(path)
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    return EvalDatasetEntry.model_validate(payload)


def load_prompt_metadata_snapshot(*, prompts_root: Path | str, prompt_id: str, prompt_version: str) -> PromptMetadataSnapshot:
    root = Path(prompts_root)
    registry_payload = _read_flat_key_value_yaml(root / "registry" / f"{prompt_id}.yaml")
    version_payload = _read_flat_key_value_yaml(root / "versions" / prompt_id / f"{prompt_version}.yaml")
    registry_record = PromptRegistryRecord.model_validate(registry_payload)
    version_record = PromptVersionRecord.model_validate(version_payload)
    return PromptMetadataSnapshot(
        promptId=registry_record.promptId,
        promptVersion=version_record.promptVersion,
        stage=registry_record.stage,
        schemaVersion=version_record.schemaVersion,
        rubricVersion=version_record.rubricVersion,
        registryStatus=registry_record.status,
        versionStatus=version_record.status,
        enabled=registry_record.enabled,
    )


def _read_flat_key_value_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise PromptAssetNotFoundError(f"YAML 文件不存在：{path}")
    payload: dict[str, Any] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line[:1].isspace() or ":" not in raw_line:
            raise PromptAssetInvalidError(f"仅支持顶层 key: value YAML：{path}:{line_number}")
        key, raw_value = raw_line.split(":", 1)
        normalized_key = key.strip()
        if not normalized_key:
            raise PromptAssetInvalidError(f"YAML key 不能为空：{path}:{line_number}")
        if normalized_key in payload:
            raise PromptAssetInvalidError(f"YAML key 重复：{path}:{line_number} -> {normalized_key}")
        payload[normalized_key] = _parse_scalar(raw_value.strip())
    return payload


def _parse_scalar(raw_value: str) -> Any:
    if raw_value in {"true", "false"}:
        return raw_value == "true"
    if raw_value in {"null", "~"}:
        return None
    if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] and raw_value[0] in {"'", '"'}:
        return raw_value[1:-1]
    return raw_value


__all__ = ["load_dataset_entry", "load_prompt_metadata_snapshot"]
