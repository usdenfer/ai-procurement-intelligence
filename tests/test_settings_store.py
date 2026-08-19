import json

import settings_store


def test_load_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(
        settings_store, "SETTINGS_FILE", tmp_path / "settings.json"
    )
    defaults = {"keywords": [], "schedule_enabled": False,
                "schedule_time": "17:00"}
    assert settings_store.load(defaults) == defaults


def test_load_overlays_persisted_values(tmp_path, monkeypatch):
    f = tmp_path / "settings.json"
    f.write_text(
        json.dumps({"keywords": ["大学"], "schedule_enabled": True},
                   ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_store, "SETTINGS_FILE", f)
    defaults = {"keywords": [], "schedule_enabled": False,
                "schedule_time": "17:00"}
    result = settings_store.load(defaults)
    assert result["keywords"] == ["大学"]
    assert result["schedule_enabled"] is True
    assert result["schedule_time"] == "17:00"


def test_save_roundtrip(tmp_path, monkeypatch):
    f = tmp_path / "settings.json"
    monkeypatch.setattr(settings_store, "SETTINGS_FILE", f)
    settings = {"keywords": ["大学"], "schedule_enabled": True,
                "schedule_time": "09:30"}
    settings_store.save(settings)
    assert json.loads(f.read_text(encoding="utf-8")) == settings


def test_load_handles_corrupt_file(tmp_path, monkeypatch):
    f = tmp_path / "settings.json"
    f.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(settings_store, "SETTINGS_FILE", f)
    defaults = {"keywords": [], "schedule_enabled": False}
    assert settings_store.load(defaults) == defaults
