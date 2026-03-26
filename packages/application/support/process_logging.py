from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any


def resolve_log_level(raw_level: str | None = None) -> int:
    if raw_level is None or not raw_level.strip():
        return logging.INFO
    resolved_name = raw_level.strip().upper()
    resolved_level = logging.getLevelName(resolved_name)
    if not isinstance(resolved_level, int):
        raise ValueError(f"不支持的日志级别：{raw_level}")
    return resolved_level


def resolve_log_dir(*, repo_root: Path, raw_path: str | None = None) -> Path:
    if raw_path is None or not raw_path.strip():
        return repo_root / "var" / "logs"
    return Path(raw_path).expanduser().resolve()


def configure_process_logging(*, service_name: str, repo_root: Path) -> Path:
    root_logger = logging.getLogger()
    configured_service = getattr(root_logger, "_novel_eval_logging_service", None)
    if configured_service == service_name:
        return getattr(root_logger, "_novel_eval_log_dir")

    log_dir = resolve_log_dir(repo_root=repo_root, raw_path=os.getenv("NOVEL_EVAL_LOG_DIR"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_level = resolve_log_level(os.getenv("NOVEL_EVAL_LOG_LEVEL"))
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.FileHandler(log_dir / f"{service_name}.log", encoding="utf-8"),
    ]
    for handler in handlers:
        handler.setFormatter(formatter)
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)
    for handler in handlers:
        root_logger.addHandler(handler)
    root_logger._novel_eval_logging_service = service_name
    root_logger._novel_eval_log_dir = log_dir
    return log_dir


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        **{
            key: _serialize_log_value(value)
            for key, value in fields.items()
            if value is not None
        },
    }
    logger.log(level, json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _serialize_log_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _serialize_log_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple | set | frozenset):
        return [_serialize_log_value(item) for item in value]
    return value
