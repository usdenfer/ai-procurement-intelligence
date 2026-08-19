"""Split cleaned documents into retrievable chunks with metadata."""
from __future__ import annotations

import re
from dataclasses import dataclass

MAX_CHUNK_CHARS = 500


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
    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    parts: list[str] = []
    current = ""
    for para in paragraphs:
        pieces = [para[i:i + limit] for i in range(0, len(para), limit)]
        for piece in pieces:
            if current and len(current) + len(piece) + 1 > limit:
                parts.append(current)
                current = piece
            else:
                current = f"{current}\n{piece}" if current else piece
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
