from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from pydantic import ValidationError

from .errors import (
    PromptAssetAmbiguityError,
    PromptAssetInvalidError,
    PromptAssetNotFoundError,
)
from .models import PromptRegistryRecord, PromptStage, PromptVersionRecord, ResolvedPrompt

_FORMAL_STAGE_DIRECTORIES = {
    "input_screening": "screening",
    "rubric_evaluation": "rubric",
    "aggregation": "aggregation",
}
_LOADABLE_REGISTRY_STATUSES = frozenset({"candidate", "active"})
_LOADABLE_VERSION_STATUSES = frozenset({"candidate", "active"})
_STATUS_PRIORITY = ("active", "candidate")
_SAFE_ASSET_NAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?$")
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
        _ensure_path_within_root(
            label="registry 目录",
            path=self._registry_root,
            root=self._prompts_root,
        )
        _ensure_path_within_root(
            label="versions 目录",
            path=self._versions_root,
            root=self._prompts_root,
        )
        _ensure_path_within_root(
            label="scoring 目录",
            path=self._scoring_root,
            root=self._prompts_root,
        )

    def resolve(
        self,
        *,
        stage: PromptStage,
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
        stage: PromptStage,
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
        narrowed_candidates = _prefer_status(narrowed_candidates)
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
        safe_path = _ensure_path_within_root(
            label="registry YAML",
            path=path,
            root=self._registry_root,
        )
        payload = _read_flat_yaml(safe_path)
        _ensure_required_fields(payload=payload, required_fields=_REQUIRED_REGISTRY_FIELDS, path=safe_path)
        record = _build_registry_record(payload=payload, path=safe_path)
        _ensure_safe_asset_name(label="promptId", value=record.promptId)
        _ensure_file_stem_matches_value(
            label="promptId",
            expected_value=safe_path.stem,
            actual_value=record.promptId,
            path=safe_path,
        )
        return record

    def _select_version_record(self, registry_record: PromptRegistryRecord) -> PromptVersionRecord:
        version_root = _ensure_path_within_root(
            label="version 目录",
            path=self._versions_root / registry_record.promptId,
            root=self._versions_root,
        )
        if not version_root.exists():
            raise PromptAssetNotFoundError(f"version 目录不存在：{version_root}")
        version_records = [self._load_version_record(path) for path in sorted(version_root.glob("*.yaml"))]
        loadable_versions = [record for record in version_records if record.status in _LOADABLE_VERSION_STATUSES]
        if not loadable_versions:
            raise PromptAssetNotFoundError(
                f"Prompt {registry_record.promptId} 没有可加载的 version 记录，需存在 active 或 candidate。"
            )
        preferred_versions = _prefer_status(loadable_versions)
        if len(preferred_versions) > 1:
            prompt_versions = ", ".join(record.promptVersion for record in preferred_versions)
            raise PromptAssetAmbiguityError(
                f"Prompt {registry_record.promptId} 存在多个同优先级可加载版本：{prompt_versions}"
            )
        version_record = preferred_versions[0]
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
        safe_path = _ensure_path_within_root(
            label="version YAML",
            path=path,
            root=self._versions_root,
        )
        payload = _read_flat_yaml(safe_path)
        _ensure_required_fields(payload=payload, required_fields=_REQUIRED_VERSION_FIELDS, path=safe_path)
        record = _build_version_record(payload=payload, path=safe_path)
        _ensure_file_stem_matches_value(
            label="promptVersion",
            expected_value=safe_path.stem,
            actual_value=record.promptVersion,
            path=safe_path,
        )
        return record

    def _read_prompt_body(self, *, stage: PromptStage, prompt_id: str, prompt_version: str) -> str:
        stage_directory = _FORMAL_STAGE_DIRECTORIES.get(stage)
        if stage_directory is None:
            raise PromptAssetNotFoundError(f"stage={stage} 没有正式 scoring 目录映射。")
        body_path = _ensure_path_within_root(
            label="Markdown 正文",
            path=self._scoring_root / stage_directory / prompt_id / f"{prompt_version}.md",
            root=self._scoring_root,
        )
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


def _prefer_status(
    records: list[PromptRegistryRecord] | list[PromptVersionRecord],
) -> list[PromptRegistryRecord] | list[PromptVersionRecord]:
    for status in _STATUS_PRIORITY:
        prioritized = [record for record in records if record.status == status]
        if prioritized:
            return prioritized
    return records


def _build_registry_record(*, payload: dict[str, Any], path: Path) -> PromptRegistryRecord:
    try:
        return PromptRegistryRecord(**payload)
    except ValidationError as error:
        raise PromptAssetInvalidError(f"registry 元数据非法：{path} -> {error}") from error


def _build_version_record(*, payload: dict[str, Any], path: Path) -> PromptVersionRecord:
    try:
        return PromptVersionRecord(**payload)
    except ValidationError as error:
        raise PromptAssetInvalidError(f"version 元数据非法：{path} -> {error}") from error


def _ensure_file_stem_matches_value(*, label: str, expected_value: str, actual_value: str, path: Path) -> None:
    if expected_value != actual_value:
        raise PromptAssetInvalidError(
            f"{label} 与文件名不一致：{path} -> {expected_value} != {actual_value}"
        )


def _ensure_path_within_root(*, label: str, path: Path, root: Path) -> Path:
    resolved_root = root.resolve()
    resolved_path = path.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise PromptAssetInvalidError(f"{label} 超出允许目录边界：{resolved_path}") from error
    return resolved_path


def _ensure_required_fields(*, payload: dict[str, Any], required_fields: tuple[str, ...], path: Path) -> None:
    missing_fields = [field_name for field_name in required_fields if field_name not in payload]
    if missing_fields:
        joined = ", ".join(missing_fields)
        raise PromptAssetInvalidError(f"YAML 缺少必填字段：{path} -> {joined}")


def _ensure_safe_asset_name(*, label: str, value: str) -> None:
    if not value or any(token in value for token in ("/", "\\", "..")):
        raise PromptAssetInvalidError(f"{label} 包含非法路径片段：{value}")
    if value in {".", ".."} or value.endswith((".", " ")):
        raise PromptAssetInvalidError(f"{label} 包含非法资产名：{value}")
    if not _SAFE_ASSET_NAME_PATTERN.fullmatch(value):
        raise PromptAssetInvalidError(f"{label} 包含非法资产名：{value}")


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
