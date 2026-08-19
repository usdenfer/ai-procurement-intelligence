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


def test_recent_days_default(monkeypatch):
    monkeypatch.delenv("AI_PROC_RECENT_DAYS", raising=False)
    assert config.recent_days() == 30


def test_recent_days_env_override(monkeypatch):
    monkeypatch.setenv("AI_PROC_RECENT_DAYS", "90")
    assert config.recent_days() == 90


def test_recent_days_invalid_falls_back(monkeypatch):
    monkeypatch.setenv("AI_PROC_RECENT_DAYS", "bad")
    assert config.recent_days() == 30
    monkeypatch.setenv("AI_PROC_RECENT_DAYS", "0")
    assert config.recent_days() == 30


def test_max_windows_default_and_override(monkeypatch):
    monkeypatch.delenv("AI_PROC_MAX_WINDOWS", raising=False)
    assert config.max_windows() == 60
    monkeypatch.setenv("AI_PROC_MAX_WINDOWS", "100")
    assert config.max_windows() == 100
    monkeypatch.setenv("AI_PROC_MAX_WINDOWS", "bad")
    assert config.max_windows() == 60


def test_full_sweep(monkeypatch):
    monkeypatch.delenv("AI_PROC_FULL_SWEEP", raising=False)
    assert config.full_sweep() is False
    monkeypatch.setenv("AI_PROC_FULL_SWEEP", "1")
    assert config.full_sweep() is True


def test_start_urls_default(monkeypatch):
    monkeypatch.delenv("AI_PROC_START_URLS", raising=False)
    assert config.start_urls() == ["http://www.yngp.com/"]


def test_start_urls_env_override(monkeypatch):
    monkeypatch.setenv(
        "AI_PROC_START_URLS",
        " http://www.yngp.com/ , https://www.zycg.gov.cn/ ",
    )
    assert config.start_urls() == [
        "http://www.yngp.com/",
        "https://www.zycg.gov.cn/",
    ]


def test_interval_hours_default_and_override(monkeypatch):
    monkeypatch.delenv("AI_PROC_INTERVAL_HOURS", raising=False)
    assert config.interval_hours() == 24.0
    monkeypatch.setenv("AI_PROC_INTERVAL_HOURS", "6")
    assert config.interval_hours() == 6.0
    monkeypatch.setenv("AI_PROC_INTERVAL_HOURS", "bad")
    assert config.interval_hours() == 24.0


def test_schedule_enabled(monkeypatch):
    monkeypatch.delenv("AI_PROC_SCHEDULE_ENABLED", raising=False)
    assert config.schedule_enabled() is False
    monkeypatch.setenv("AI_PROC_SCHEDULE_ENABLED", "1")
    assert config.schedule_enabled() is True
    monkeypatch.setenv("AI_PROC_SCHEDULE_ENABLED", "no")
    assert config.schedule_enabled() is False
