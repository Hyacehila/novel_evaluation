from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
API_SRC = Path(__file__).resolve().parents[1] / "src"

for path in (REPO_ROOT, API_SRC):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
