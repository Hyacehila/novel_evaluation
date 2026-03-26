from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import (
    PromptAssetAmbiguityError,
    PromptAssetInvalidError,
    PromptAssetNotFoundError,
)
from .models import PromptRegistryRecord, PromptVersionRecord, ResolvedPrompt

_FORMAL_STAGE_DIRECTORIES = {
    "input_screening": "screening",
    "rubric_evaluation": "rubric",
    "aggregation": "aggregation",
}
_LOADABLE_REGISTRY_STATUSES = frozenset({"candidate", "active"})
_LOADABLE_VERSION_STATUSES = frozenset({"candidate", "active"})
_WILDCARD_SCOPE = "*"
_REQUIRED_REGISTRY_FIELDS = (
    "promptId",
    "stage",
    "status",
    "schemaVersion",
    "rubricVersion",
    "inputCompositionScope",
    "evaluationModeScope",
    "providerScope",
    "modelScope",
    "enabled",
)
_REQUIRED_VERSION_FIELDS = (
    "promptId",
    "promptVersion",
    "status",
    "schemaVersion",
    "rubricVersion",
    "owner",
    "updatedAt",
    "changeSummary",
    "rollbackTarget",
    "evalRequirement",
)


class FilePromptRuntime:
    def __init__(self, *, prompts_root: Path | str) -> None:
        self._prompts_root = Path(prompts_root).resolve()
        self._registry_root = self._prompts_root / "registry"
        self._versions_root = self._prompts_root / "versions"
        self._scoring_root = self._prompts_root / "scoring"

    def resolve(
        self,
        *,
        stage: str,
        input_composition: str,
        evaluation_mode: str,
        provider_id: str,
        model_id: str,
    ) -> ResolvedPrompt:
        registry_record = self._select_registry_record(
            stage=stage,
            input_composition=input_composition,
            evaluation_mode=evaluation_mode,
            provider_id=provider_id,
            model_id=model_id,
        )
        version_record = self._select_version_record(registry_record)
        body = self._read_prompt_body(
            stage=registry_record.stage,
            prompt_id=registry_record.promptId,
            prompt_version=version_record.promptVersion,
        )
        return ResolvedPrompt(
            promptId=registry_record.promptId,
            promptVersion=version_record.promptVersion,
            body=body,
            schemaVersion=version_record.schemaVersion,
            rubricVersion=version_record.rubricVersion,
        )

    def _select_registry_record(
        self,
        *,
        stage: str,
        input_composition: str,
        evaluation_mode: str,
        provider_id: str,
        model_id: str,
    ) -> PromptRegistryRecord:
        registry_records = self._load_registry_records()
        stage_candidates = [record for record in registry_records if record.stage == stage]
        if not stage_candidates:
            raise PromptAssetNotFoundError(f"未找到 stage={stage} 的 registry 资产。")

        loadable_stage_candidates = [
            record for record in stage_candidates if record.status in _LOADABLE_REGISTRY_STATUSES
        ]
        if not loadable_stage_candidates:
            raise PromptAssetNotFoundError(
                f"stage={stage} 没有处于 candidate 或 active 的 registry 资产。"
            )

        narrowed_candidates = loadable_stage_candidates
        narrowed_candidates = self._narrow_by_scope(
            narrowed_candidates,
            scope_field="inputCompositionScope",
            request_value=input_composition,
            label="inputCompositionScope",
        )
        narrowed_candidates = self._narrow_by_scope(
            narrowed_candidates,
            scope_field="evaluationModeScope",
            request_value=evaluation_mode,
            label="evaluationModeScope",
        )
        narrowed_candidates = self._narrow_by_scope(
            narrowed_candidates,
            scope_field="providerScope",
            request_value=provider_id,
            label="providerScope",
        )
        narrowed_candidates = self._narrow_by_scope(
            narrowed_candidates,
            scope_field="modelScope",
            request_value=model_id,
            label="modelScope",
        )
        enabled_candidates = [record for record in narrowed_candidates if record.enabled]
        if not enabled_candidates:
            prompt_ids = ", ".join(record.promptId for record in narrowed_candidates)
            raise PromptAssetNotFoundError(
                f"候选 Prompt 已匹配到 enabled 判定，但没有启用资产。stage={stage}, prompts=[{prompt_ids}]"
            )
        if len(enabled_candidates) > 1:
            prompt_ids = ", ".join(record.promptId for record in enabled_candidates)
            raise PromptAssetAmbiguityError(f"Prompt registry 选择不唯一：{prompt_ids}")
        return enabled_candidates[0]

    def _load_registry_records(self) -> tuple[PromptRegistryRecord, ...]:
        if not self._registry_root.exists():
            raise PromptAssetNotFoundError(f"registry 目录不存在：{self._registry_root}")
        records = [self._load_registry_record(path) for path in sorted(self._registry_root.glob("*.yaml"))]
        if not records:
            raise PromptAssetNotFoundError(f"registry 目录下没有 YAML 资产：{self._registry_root}")
        return tuple(records)

    def _load_registry_record(self, path: Path) -> PromptRegistryRecord:
        payload = _read_flat_yaml(path)
        _ensure_required_fields(payload=payload, required_fields=_REQUIRED_REGISTRY_FIELDS, path=path)
        record = PromptRegistryRecord(**payload)
        _ensure_safe_asset_name(label="promptId", value=record.promptId)
        return record

    def _select_version_record(self, registry_record: PromptRegistryRecord) -> PromptVersionRecord:
        version_root = self._versions_root / registry_record.promptId
        if not version_root.exists():
            raise PromptAssetNotFoundError(f"version 目录不存在：{version_root}")
        version_records = [self._load_version_record(path) for path in sorted(version_root.glob("*.yaml"))]
        loadable_versions = [record for record in version_records if record.status in _LOADABLE_VERSION_STATUSES]
        if not loadable_versions:
            raise PromptAssetNotFoundError(
                f"Prompt {registry_record.promptId} 没有可加载的 version 记录，需存在 active 或 candidate。"
            )
        if len(loadable_versions) > 1:
            prompt_versions = ", ".join(record.promptVersion for record in loadable_versions)
            raise PromptAssetAmbiguityError(
                f"Prompt {registry_record.promptId} 存在多个可加载版本：{prompt_versions}"
            )
        version_record = loadable_versions[0]
        if version_record.promptId != registry_record.promptId:
            raise PromptAssetInvalidError(
                f"version 元数据 promptId 与 registry 不一致：{version_record.promptId} != {registry_record.promptId}"
            )
        if version_record.schemaVersion != registry_record.schemaVersion:
            raise PromptAssetInvalidError(
                f"schemaVersion 不一致：{version_record.schemaVersion} != {registry_record.schemaVersion}"
            )
        if version_record.rubricVersion != registry_record.rubricVersion:
            raise PromptAssetInvalidError(
                f"rubricVersion 不一致：{version_record.rubricVersion} != {registry_record.rubricVersion}"
            )
        _ensure_safe_asset_name(label="promptVersion", value=version_record.promptVersion)
        return version_record

    def _load_version_record(self, path: Path) -> PromptVersionRecord:
        payload = _read_flat_yaml(path)
        _ensure_required_fields(payload=payload, required_fields=_REQUIRED_VERSION_FIELDS, path=path)
        return PromptVersionRecord(**payload)

    def _read_prompt_body(self, *, stage: str, prompt_id: str, prompt_version: str) -> str:
        stage_directory = _FORMAL_STAGE_DIRECTORIES.get(stage)
        if stage_directory is None:
            raise PromptAssetNotFoundError(f"stage={stage} 没有正式 scoring 目录映射。")
        body_path = self._scoring_root / stage_directory / prompt_id / f"{prompt_version}.md"
        if not body_path.exists():
            raise PromptAssetNotFoundError(f"Markdown 正文不存在：{body_path}")
        body = body_path.read_text(encoding="utf-8")
        if not body.strip():
            raise PromptAssetInvalidError(f"Markdown 正文为空：{body_path}")
        return body

    def _narrow_by_scope(
        self,
        candidates: list[PromptRegistryRecord],
        *,
        scope_field: str,
        request_value: str,
        label: str,
    ) -> list[PromptRegistryRecord]:
        matching_candidates = [
            record
            for record in candidates
            if _scope_matches(getattr(record, scope_field), request_value)
        ]
        if not matching_candidates:
            raise PromptAssetNotFoundError(f"没有匹配 {label}={request_value} 的 Prompt 资产。")
        exact_candidates = [
            record for record in matching_candidates if getattr(record, scope_field) == request_value
        ]
        return exact_candidates if exact_candidates else matching_candidates



def _scope_matches(scope_value: str, request_value: str) -> bool:
    return scope_value == request_value or scope_value == _WILDCARD_SCOPE



def _ensure_required_fields(*, payload: dict[str, Any], required_fields: tuple[str, ...], path: Path) -> None:
    missing_fields = [field_name for field_name in required_fields if field_name not in payload]
    if missing_fields:
        joined = ", ".join(missing_fields)
        raise PromptAssetInvalidError(f"YAML 缺少必填字段：{path} -> {joined}")



def _ensure_safe_asset_name(*, label: str, value: str) -> None:
    if not value or any(token in value for token in ("/", "\\", "..")):
        raise PromptAssetInvalidError(f"{label} 包含非法路径片段：{value}")



def _read_flat_yaml(path: Path) -> dict[str, Any]:
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
