from bs4 import BeautifulSoup

import clean


class FakeDoc:
    def __init__(self, summary):
        self._summary = summary

    def summary(self):
        return self._summary


def test_clean_text_uses_readability_when_available(monkeypatch):
    monkeypatch.setattr(
        clean, "Document",
        lambda html: FakeDoc("<html><body><article>正文内容</article></body></html>"),
    )
    assert "正文内容" in clean.clean_text("<html>raw</html>")


def test_clean_text_falls_back_to_visible_text_when_readability_missing(monkeypatch):
    monkeypatch.setattr(clean, "Document", None)
    html = "<html><body><script>var x</script><p>可见文本</p></body></html>"
    assert clean.clean_text(html) == "可见文本"


def test_clean_text_falls_back_when_summary_empty(monkeypatch):
    monkeypatch.setattr(clean, "Document", lambda html: FakeDoc(""))
    html = "<html><body><p>兜底正文</p></body></html>"
    assert clean.clean_text(html) == "兜底正文"


def test_clean_text_falls_back_when_document_raises(monkeypatch):
    def boom(html):
        raise RuntimeError("parse failed")

    monkeypatch.setattr(clean, "Document", boom)
    html = "<html><body><p>异常兜底</p></body></html>"
    assert clean.clean_text(html) == "异常兜底"
