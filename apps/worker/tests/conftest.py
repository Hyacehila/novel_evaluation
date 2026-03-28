from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER_SRC = Path(__file__).resolve().parents[1] / "src"
API_SRC = REPO_ROOT / "apps" / "api" / "src"
PROMPT_RUNTIME_SRC = REPO_ROOT / "packages" / "prompt-runtime" / "src"
PROVIDER_ADAPTERS_SRC = REPO_ROOT / "packages" / "provider-adapters" / "src"

for path in reversed((REPO_ROOT, WORKER_SRC, API_SRC, PROMPT_RUNTIME_SRC, PROVIDER_ADAPTERS_SRC)):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
