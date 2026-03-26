from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from packages.schemas.evals import EvalBaseline, EvalRecord, EvalReport


class EvalPathError(ValueError):
    pass


_ModelT = TypeVar("_ModelT", EvalBaseline, EvalReport)


def write_baseline(*, root: Path | str, baseline: EvalBaseline) -> Path:
    resolved_root = _resolve_evals_root(root)
    target_path = resolved_root / "baselines" / f"{baseline.baselineId}.json"
    return _write_model(target_path=target_path, model=baseline, overwrite=False)


def write_report(*, root: Path | str, report: EvalReport) -> Path:
    resolved_root = _resolve_evals_root(root)
    target_path = resolved_root / "reports" / f"{report.reportId}.json"
    return _write_model(target_path=target_path, model=report, overwrite=True)


def write_records(*, root: Path | str, report_id: str, records: tuple[EvalRecord, ...]) -> Path:
    resolved_root = _resolve_evals_root(root)
    target_path = resolved_root / "reports" / f"{report_id}.records.json"
    payload = [record.model_dump(mode="json") for record in records]
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_path


def load_baseline(path: Path | str) -> EvalBaseline:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return EvalBaseline.model_validate(payload)


def load_report(path: Path | str) -> EvalReport:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return EvalReport.model_validate(payload)


def _resolve_evals_root(root: Path | str) -> Path:
    resolved_root = Path(root).resolve()
    if resolved_root.name != "evals":
        raise EvalPathError("root 必须指向 evals 目录。")
    return resolved_root


def _write_model(*, target_path: Path, model: _ModelT, overwrite: bool) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists() and not overwrite:
        raise FileExistsError(f"文件已存在：{target_path}")
    payload = model.model_dump(mode="json")
    target_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target_path


__all__ = [
    "EvalPathError",
    "load_baseline",
    "load_report",
    "write_baseline",
    "write_records",
    "write_report",
]
