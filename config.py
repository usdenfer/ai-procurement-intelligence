"""Runtime configuration via environment variables."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def embedding_base_url() -> str:
    return os.environ.get(
        "EMBEDDING_BASE_URL",
        os.environ.get("AI_BASE_URL", "https://api.vectorengine.cn/v1"),
    )


def embedding_model() -> str:
    return os.environ.get("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")


def embedding_api_key() -> str:
    return os.environ.get("EMBEDDING_API_KEY", os.environ.get("DEEPSEEK_API_KEY", ""))


def data_dir() -> str:
    return os.environ.get("AI_PROC_DATA_DIR", "data")


DEFAULT_KEYWORDS = ["大学", "学院", "高校", "学校", "职业院校", "高职"]


def search_keywords() -> list[str]:
    raw = os.environ.get("AI_PROC_KEYWORDS", "")
    keywords = [k.strip() for k in raw.split(",") if k.strip()]
    return keywords or DEFAULT_KEYWORDS


DEFAULT_QUERY_TYPES = ("23", "1", "3")


def query_types() -> tuple[str, ...]:
    raw = os.environ.get("AI_PROC_QUERY_TYPES", "")
    types = tuple(t.strip() for t in raw.split(",") if t.strip())
    return types or DEFAULT_QUERY_TYPES


DEFAULT_RECENT_DAYS = 30


def recent_days() -> int:
    raw = os.environ.get("AI_PROC_RECENT_DAYS", "")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_RECENT_DAYS
    return value if value > 0 else DEFAULT_RECENT_DAYS
