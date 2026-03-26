from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_RUNTIME_SRC = REPO_ROOT / "packages" / "prompt-runtime" / "src"

for path in (REPO_ROOT, PROMPT_RUNTIME_SRC):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
