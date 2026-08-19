"""Orchestrate source -> clean -> chunk -> embed -> store."""
from __future__ import annotations

from clean import clean_text
from chunk import chunk_document
from embed import embed
from store import Store


async def ingest(source, store: Store, embed_fn=embed) -> dict:
    """Consume (url, html, title, date) pages into the store.

    Returns counts: {"documents": int, "chunks": int, "errors": int}.
    """
    counts = {"documents": 0, "chunks": 0, "errors": 0}
    async for url, html, title, date in source:
        try:
            text = clean_text(html)
            chunks = chunk_document(url, text, title, date)
            if not chunks:
                continue
            vectors = await embed_fn([c.text for c in chunks])
            doc_id = store.save_document(url, text, title, date)
            store.upsert_chunks(doc_id, chunks, vectors)
            counts["documents"] += 1
            counts["chunks"] += len(chunks)
        except Exception:
            counts["errors"] += 1
    return counts
