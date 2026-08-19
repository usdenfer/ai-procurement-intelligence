import asyncio

import chromadb

import ask
import store
from store import Store
from chunk import Chunk


def make_store(tmp_path):
    return Store(root=str(tmp_path), chroma_client=chromadb.Client())


def seed(store):
    doc_id = store.save_document(
        "https://x.test/a", "某学校设备采购项目，预算 120 万元", "设备采购", "2026-08-01")
    store.upsert_chunks(doc_id, [
        Chunk(text="某学校设备采购项目，预算 120 万元", url="https://x.test/a",
              title="设备采购", published_date="2026-08-01", index=0)],
        [[1.0, 0.0]])


def test_ask_builds_answer_with_sources(tmp_path, monkeypatch):
    s = make_store(tmp_path)
    seed(s)

    captured = {}

    async def fake_embed(texts):
        return [[1.0, 0.0]]

    async def fake_chat(messages, max_tokens=4000, timeout=180.0):
        captured["messages"] = messages
        return "答案是预算 120 万元。"

    monkeypatch.setattr(ask, "embed", fake_embed)
    monkeypatch.setattr(ask, "chat", fake_chat)

    result = asyncio.run(ask.ask("预算多少？", s))
    assert result["answer"] == "答案是预算 120 万元。"
    assert "https://x.test/a" in result["sources"]
    user_content = captured["messages"][-1]["content"]
    assert "预算多少？" in user_content
    assert "https://x.test/a" in user_content


def test_ask_returns_empty_when_no_results(tmp_path, monkeypatch):
    s = make_store(tmp_path)

    async def fake_embed(texts):
        return [[1.0, 0.0]]

    monkeypatch.setattr(ask, "embed", fake_embed)
    result = asyncio.run(ask.ask("预算多少？", s))
    assert result["answer"] == "知识库中未找到相关内容。"
    assert result["sources"] == []
