import config


def test_embedding_defaults(monkeypatch):
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert config.embedding_base_url() == "https://api.vectorengine.cn/v1"
    assert config.embedding_model() == "bge-large-zh"
    assert config.embedding_api_key() == ""


def test_embedding_env_overrides(monkeypatch):
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://x.test/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "m3")
    monkeypatch.setenv("EMBEDDING_API_KEY", "sk-abc")
    assert config.embedding_base_url() == "https://x.test/v1"
    assert config.embedding_model() == "m3"
    assert config.embedding_api_key() == "sk-abc"


def test_embedding_api_key_falls_back_to_deepseek(monkeypatch):
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
    assert config.embedding_api_key() == "sk-ds"
