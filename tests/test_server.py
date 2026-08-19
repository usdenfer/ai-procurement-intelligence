from fastapi.testclient import TestClient

import server


def test_index_returns_html():
    client = TestClient(server.app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI 采购情报" in resp.text


def test_stats_returns_document_count(tmp_path, monkeypatch):
    import store

    monkeypatch.setattr(store, "data_dir", lambda: str(tmp_path))
    client = TestClient(server.app)
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    assert resp.json()["documents"] == 0


def test_ask_empty_question_short_circuits():
    client = TestClient(server.app)
    resp = client.post("/api/ask", json={"question": "   "})
    assert resp.status_code == 200
    assert resp.json() == {"answer": "问题不能为空。", "sources": []}


def test_ingest_status_endpoint():
    client = TestClient(server.app)
    resp = client.get("/api/ingest/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "idle"
