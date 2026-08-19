import chromadb

import store
from chunk import Chunk


def make_store(tmp_path):
    client = chromadb.Client()  # in-memory, no onnx model download
    return store.Store(root=str(tmp_path), chroma_client=client)


def test_save_document_is_idempotent(tmp_path):
    s = make_store(tmp_path)
    doc_id = s.save_document("https://x.test/a", "正文", "标题", "2026-08-01")
    assert doc_id == s.save_document("https://x.test/a", "新正文", "新标题", "2026-08-02")
    row = s.conn.execute(
        "SELECT clean_text, title FROM documents WHERE id=?", (doc_id,)
    ).fetchone()
    assert row == ("新正文", "新标题")


def test_upsert_chunks_and_query(tmp_path):
    s = make_store(tmp_path)
    doc_id = s.save_document("https://x.test/a", "正文", "标题", "2026-08-01")
    chunks = [Chunk(text="第一块", url="https://x.test/a",
                    title="标题", published_date="2026-08-01", index=0)]
    s.upsert_chunks(doc_id, chunks, [[0.1, 0.2]])
    results = s.query([0.1, 0.2], top_k=1)
    assert len(results) == 1
    assert results[0]["text"] == "第一块"
    assert results[0]["url"] == "https://x.test/a"


def test_upsert_chunks_no_chunks_is_noop(tmp_path):
    s = make_store(tmp_path)
    s.upsert_chunks("doc", [], [])
    assert s.query([0.0, 0.0], top_k=1) == []
