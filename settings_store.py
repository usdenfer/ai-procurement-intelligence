"""Persist user settings to a JSON file next to the project."""
from __future__ import annotations

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"


def load(defaults: dict) -> dict:
    """Return defaults overlaid with persisted settings.json values."""
    result = dict(defaults)
    if not SETTINGS_FILE.exists():
        return result
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return result
    if isinstance(data, dict):
        for key in defaults:
            if key in data:
                result[key] = data[key]
    return result


def save(settings: dict) -> None:
    """Write settings to settings.json atomically-ish."""
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
