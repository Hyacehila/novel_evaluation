from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
API_SRC = Path(__file__).resolve().parents[1] / "src"

for path in (REPO_ROOT, API_SRC):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)


@pytest.fixture(autouse=True)
def isolate_runtime_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from api.dependencies import get_evaluation_service, get_task_repository

    monkeypatch.setenv("NOVEL_EVAL_DB_PATH", str(tmp_path / "test.sqlite3"))
    get_evaluation_service.cache_clear()
    get_task_repository.cache_clear()
    yield
    get_evaluation_service.cache_clear()
    get_task_repository.cache_clear()
