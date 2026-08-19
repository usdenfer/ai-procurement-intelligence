"""Split cleaned documents into retrievable chunks with metadata."""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_CHUNK_CHARS = 1500


@dataclass
class Chunk:
    text: str
    url: str
    title: str
    published_date: str
    index: int

    def metadata(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "published_date": self.published_date,
            "chunk_index": self.index,
        }


def _split_long_text(text: str, limit: int = MAX_CHUNK_CHARS) -> list[str]:
    if len(text) <= limit:
        return [text]
    paragraphs = re.split(r"\n+", text)
    parts: list[str] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current and len(current) + len(para) + 1 > limit:
            parts.append(current)
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current:
        parts.append(current)
    return parts


def chunk_document(
    url: str,
    clean_text: str,
    title: str = "",
    published_date: str = "",
) -> list[Chunk]:
    parts = _split_long_text(clean_text)
    return [
        Chunk(text=part, url=url, title=title,
              published_date=published_date, index=i)
        for i, part in enumerate(parts)
        if part.strip()
    ]
