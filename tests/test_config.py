import config


def test_embedding_defaults(monkeypatch):
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("AI_BASE_URL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    assert config.embedding_base_url() == "https://api.vectorengine.cn/v1"
    assert config.embedding_model() == "BAAI/bge-large-zh-v1.5"
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


def test_embedding_base_url_falls_back_to_ai_base_url(monkeypatch):
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    monkeypatch.setenv("AI_BASE_URL", "https://ai.test/v1")
    assert config.embedding_base_url() == "https://ai.test/v1"


def test_data_dir_default_and_override(monkeypatch):
    monkeypatch.delenv("AI_PROC_DATA_DIR", raising=False)
    assert config.data_dir() == "data"
    monkeypatch.setenv("AI_PROC_DATA_DIR", "D:/tmp/x")
    assert config.data_dir() == "D:/tmp/x"


def test_search_keywords_default(monkeypatch):
    monkeypatch.delenv("AI_PROC_KEYWORDS", raising=False)
    assert config.search_keywords() == ["大学", "学院", "高校", "学校", "职业院校", "高职"]


def test_search_keywords_env_override(monkeypatch):
    monkeypatch.setenv("AI_PROC_KEYWORDS", " 教育 , 设备,采购 ")
    assert config.search_keywords() == ["教育", "设备", "采购"]


def test_search_keywords_empty_env_falls_back(monkeypatch):
    monkeypatch.setenv("AI_PROC_KEYWORDS", "  , ")
    assert config.search_keywords() == ["大学", "学院", "高校", "学校", "职业院校", "高职"]


def test_query_types_default(monkeypatch):
    monkeypatch.delenv("AI_PROC_QUERY_TYPES", raising=False)
    assert config.query_types() == ("23", "1", "3")


def test_query_types_env_override(monkeypatch):
    monkeypatch.setenv("AI_PROC_QUERY_TYPES", " 23 , 1 ")
    assert config.query_types() == ("23", "1")
