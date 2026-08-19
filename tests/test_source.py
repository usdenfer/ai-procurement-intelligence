import asyncio

import _bootstrap
_bootstrap.ensure_wkc()

import crawler
import discovery
import source
from discovery.models import DiscoveryStats


def _collect(coro):
    async def run():
        return [x async for x in coro]

    return asyncio.run(run())


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


def test_yngp_pages_forwards_keywords(monkeypatch):
    homepage = crawler.CrawledPage(
        url="http://www.yngp.com/", html="<html></html>"
    )
    article = crawler.CrawledPage(
        url="http://www.yngp.com/showBulletinInfo.html?bulletin_id=1",
        html="<html><title>公告一</title><body>x</body></html>",
    )

    async def fake_crawl(start_url, depth=1, render=False, **kwargs):
        assert start_url == "http://www.yngp.com/"
        return crawler.CrawlResult(pages=[homepage])

    async def fake_discover(start_url, keywords, base_result, depth,
                            render_mode, **kwargs):
        assert keywords == ["大学", "学院"]
        assert base_result.pages[0].url == homepage.url
        return discovery.DiscoveryRun(
            pages=[article], failed=[], stats=DiscoveryStats(), candidates=[]
        )

    monkeypatch.setattr(crawler, "crawl", fake_crawl)
    monkeypatch.setattr(discovery, "discover_pages", fake_discover)

    pages = _collect(source.yngp_pages(["大学", "学院"]))
    assert pages == [(article.url, article.html, "公告一", "")]


def test_yngp_pages_defaults_to_configured_keywords(monkeypatch):
    import config

    homepage = crawler.CrawledPage(
        url="http://www.yngp.com/", html="<html></html>"
    )
    monkeypatch.setattr(config, "search_keywords", lambda: ["测试词"])

    async def fake_crawl(start_url, depth=1, render=False, **kwargs):
        return crawler.CrawlResult(pages=[homepage])

    captured = {}

    async def fake_discover(start_url, keywords, base_result, depth,
                            render_mode, **kwargs):
        captured["keywords"] = keywords
        return discovery.DiscoveryRun(
            pages=[], failed=[], stats=DiscoveryStats(), candidates=[]
        )

    monkeypatch.setattr(crawler, "crawl", fake_crawl)
    monkeypatch.setattr(discovery, "discover_pages", fake_discover)

    assert _collect(source.yngp_pages()) == []
    assert captured["keywords"] == ["测试词"]

