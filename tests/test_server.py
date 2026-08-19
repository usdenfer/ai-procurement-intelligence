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


def test_get_settings_returns_fields():
    client = TestClient(server.app)
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    d = resp.json()
    for key in ("keywords", "start_urls", "schedule_enabled",
                "schedule_time", "next_run"):
        assert key in d


def test_update_settings(monkeypatch):
    server._settings.update(
        keywords=[], start_urls=[], schedule_enabled=False, schedule_time="17:00"
    )
    client = TestClient(server.app)
    resp = client.post("/api/settings", json={
        "keywords": ["大学"],
        "start_urls": ["http://www.yngp.com/"],
        "schedule_enabled": True,
        "schedule_time": "09:30",
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["keywords"] == ["大学"]
    assert d["start_urls"] == ["http://www.yngp.com/"]
    assert d["schedule_enabled"] is True
    assert d["schedule_time"] == "09:30"


def test_update_settings_invalid_time_falls_back():
    server._settings.update(schedule_time="17:00")
    client = TestClient(server.app)
    resp = client.post("/api/settings", json={"schedule_time": "25:99"})
    assert resp.status_code == 200
    assert resp.json()["schedule_time"] == "17:00"
