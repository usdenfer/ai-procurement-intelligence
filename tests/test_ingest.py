import asyncio

import chromadb

import ingest
import store
from store import Store


class FakeSource:
    def __init__(self, pages):
        self._pages = pages

    async def __aiter__(self):
        for p in self._pages:
            yield p


async def _embed_fake(texts):
    return [[0.0] * 3 for _ in texts]


def make_store(tmp_path):
    return Store(root=str(tmp_path), chroma_client=chromadb.Client())


def test_ingest_persists_documents_and_chunks(tmp_path, monkeypatch):
    pages = [
        ("https://x.test/a", "<html><p>公告正文A</p></html>", "标题A", "2026-08-01"),
        ("https://x.test/b", "<html><p>公告正文B</p></html>", "标题B", "2026-08-02"),
    ]
    s = make_store(tmp_path)
    counts = asyncio.run(ingest.ingest(FakeSource(pages), s, _embed_fake))
    assert counts == {"documents": 2, "chunks": 2, "errors": 0}
    row = s.conn.execute(
        "SELECT COUNT(*) FROM documents"
    ).fetchone()
    assert row[0] == 2
    assert s.collection.count() == 2


def test_ingest_skips_failed_clean_but_keeps_others(tmp_path, monkeypatch):
    def broken_clean(html):
        raise RuntimeError("clean failed")

    monkeypatch.setattr(ingest, "clean_text", broken_clean)
    pages = [("https://x.test/a", "<html>x</html>", "", "")]
    s = make_store(tmp_path)
    counts = asyncio.run(ingest.ingest(FakeSource(pages), s, _embed_fake))
    assert counts == {"documents": 0, "chunks": 0, "errors": 1}


def test_ingest_skips_failed_embed_but_keeps_others(tmp_path, monkeypatch):
    async def broken_embed(texts):
        raise RuntimeError("embed failed")

    pages = [("https://x.test/a", "<html><p>x</p></html>", "", "")]
    s = make_store(tmp_path)
    counts = asyncio.run(ingest.ingest(FakeSource(pages), s, broken_embed))
    assert counts == {"documents": 0, "chunks": 0, "errors": 1}
