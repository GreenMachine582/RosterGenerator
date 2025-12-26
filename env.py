from __future__ import annotations

import os
from pathlib import Path


def load_env(path: Path | None = None) -> None:
    """
    - Ignores comments and empty lines
    - Does not overwrite existing env vars
    """
    if path is None:
        path = Path(".env")

    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())
