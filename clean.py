"""HTML main-content extraction for the RAG ingest pipeline."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

try:
    from readability import Document
except ImportError:
    Document = None


def _node_text(node) -> str:
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def _visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return _node_text(soup)


def clean_text(html: str) -> str:
    """Return clean main-content text; fall back to whole-page visible text."""
    if Document is not None:
        try:
            summary = Document(html).summary()
        except Exception:
            summary = ""
        if summary:
            text = _node_text(BeautifulSoup(summary, "html.parser"))
            if text:
                return text
    return _visible_text(html)
