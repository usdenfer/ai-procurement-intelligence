import asyncio

import _bootstrap
_bootstrap.ensure_wkc()

import crawler
import discovery
import source
from discovery.models import Candidate, DiscoveryStats


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


def test_pages_forwards_keywords_and_uses_candidate_meta(monkeypatch):
    homepage = crawler.CrawledPage(
        url="http://www.yngp.com/", html="<html></html>"
    )
    article = crawler.CrawledPage(
        url="http://www.yngp.com/showBulletinInfo.html?bulletin_id=1",
        html="<html><title>通用标题</title><body>x</body></html>",
    )
    candidate = Candidate(
        url=article.url,
        source="yngp-api",
        title_hint="某某大学设备采购项目",
        published_date="2026-08-01",
    )

    async def fake_crawl(start_url, depth=1, render=False, **kwargs):
        assert start_url == "http://www.yngp.com/"
        return crawler.CrawlResult(pages=[homepage])

    async def fake_discover(start_url, keywords, base_result, depth,
                            render_mode, **kwargs):
        assert keywords == ["大学", "学院"]
        assert kwargs["query_types"] == ("23", "1", "3")
        assert kwargs["recent_days"] == 30
        assert kwargs["max_windows_per_query"] == 60
        assert kwargs["full_sweep"] is False
        assert base_result.pages[0].url == homepage.url
        return discovery.DiscoveryRun(
            pages=[article], failed=[], stats=DiscoveryStats(),
            candidates=[candidate],
        )

    monkeypatch.setattr(crawler, "crawl", fake_crawl)
    monkeypatch.setattr(discovery, "discover_pages", fake_discover)

    pages = _collect(source.pages(["大学", "学院"]))
    assert pages == [
        (article.url, article.html, "某某大学设备采购项目", "2026-08-01")
    ]


def test_pages_falls_back_to_page_title_without_candidate(monkeypatch):
    homepage = crawler.CrawledPage(
        url="http://www.yngp.com/", html="<html></html>"
    )
    article = crawler.CrawledPage(
        url="http://www.yngp.com/showBulletinInfo.html?bulletin_id=1",
        html="<html><title>公告一</title><body>x</body></html>",
    )

    async def fake_crawl(start_url, depth=1, render=False, **kwargs):
        return crawler.CrawlResult(pages=[homepage])

    async def fake_discover(start_url, keywords, base_result, depth,
                            render_mode, **kwargs):
        return discovery.DiscoveryRun(
            pages=[article], failed=[], stats=DiscoveryStats(), candidates=[]
        )

    monkeypatch.setattr(crawler, "crawl", fake_crawl)
    monkeypatch.setattr(discovery, "discover_pages", fake_discover)

    pages = _collect(source.pages(["大学"]))
    assert pages == [(article.url, article.html, "公告一", "")]


def test_pages_defaults_to_configured_keywords(monkeypatch):
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

    assert _collect(source.pages()) == []
    assert captured["keywords"] == ["测试词"]


def test_pages_iterates_multiple_start_urls(monkeypatch):
    import config

    monkeypatch.setattr(
        config, "start_urls",
        lambda: ["http://www.yngp.com/", "https://www.zycg.gov.cn/"],
    )

    seen_urls = []

    async def fake_crawl(start_url, depth=1, render=False, **kwargs):
        return crawler.CrawlResult(
            pages=[crawler.CrawledPage(url=start_url, html="<html></html>")]
        )

    async def fake_discover(start_url, keywords, base_result, depth,
                            render_mode, **kwargs):
        seen_urls.append(start_url)
        return discovery.DiscoveryRun(
            pages=[], failed=[], stats=DiscoveryStats(), candidates=[]
        )

    monkeypatch.setattr(crawler, "crawl", fake_crawl)
    monkeypatch.setattr(discovery, "discover_pages", fake_discover)

    assert _collect(source.pages(["大学"])) == []
    assert seen_urls == ["http://www.yngp.com/", "https://www.zycg.gov.cn/"]
