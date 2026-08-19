"""Insert the sibling web_keyword_catcher repo onto sys.path for reuse."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _wkc_path() -> Path:
    override = os.environ.get("WKC_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "web_keyword_catcher"


def ensure_wkc() -> Path:
    path = _wkc_path()
    if not path.is_dir():
        raise FileNotFoundError(
            f"web_keyword_catcher not found at {path}; "
            "clone it alongside or set WKC_PATH"
        )
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    return path
