import source


def test_extract_page_fields_from_crawled_page():
    fake_page = type("P", (), {
        "url": "https://x.test/a",
        "html": "<html><title>T</title><body>x</body></html>",
    })()
    title = source._page_title(fake_page)
    assert title == "T"


def test_extract_page_fields_title_missing():
    fake_page = type("P", (), {
        "url": "https://x.test/a",
        "html": "<html><body>x</body></html>",
    })()
    assert source._page_title(fake_page) == ""
