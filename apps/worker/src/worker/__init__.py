from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
API_SRC = REPO_ROOT / "apps" / "api" / "src"
PROMPT_RUNTIME_SRC = REPO_ROOT / "packages" / "prompt-runtime" / "src"
PROVIDER_ADAPTERS_SRC = REPO_ROOT / "packages" / "provider-adapters" / "src"

for _path in (REPO_ROOT, API_SRC, PROMPT_RUNTIME_SRC, PROVIDER_ADAPTERS_SRC):
    _path_text = str(_path)
    if _path_text not in sys.path:
        sys.path.insert(0, _path_text)

__all__ = ["API_SRC", "PROMPT_RUNTIME_SRC", "PROVIDER_ADAPTERS_SRC", "REPO_ROOT"]
