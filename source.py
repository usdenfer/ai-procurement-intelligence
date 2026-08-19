"""Yield crawled procurement pages from the reused web_keyword_catcher crawler."""
from __future__ import annotations

from collections.abc import AsyncIterator

from bs4 import BeautifulSoup


def _page_title(page) -> str:
    soup = BeautifulSoup(page.html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""


async def _discover_pages(start_url, keywords):
    import _bootstrap
    _bootstrap.ensure_wkc()

    from crawler import crawl  # noqa: E402
    from discovery import discover_pages  # noqa: E402
    from discovery.urltools import normalize_candidate_url  # noqa: E402

    from config import query_types, recent_days  # noqa: E402

    base_result = await crawl(start_url, depth=1, render=False)
    return await discover_pages(
        start_url, keywords, base_result, 1, "auto",
        query_types=query_types(),
        recent_days=recent_days(),
    )


async def pages(
    keywords: list[str] | None = None,
) -> AsyncIterator[tuple[str, str, str, str]]:
    """Yield (url, html, title, published_date) across all configured sources.

    走 discovery 引擎：先用静态 BFS 抓首页建立 base_result（用于识别站点
    适配器），再让适配器对应的 Provider 用给定关键词发现候选并抓取正文。
    标题与发布日期取自候选元数据（Candidate.title_hint / published_date），
    详情页 <title> 仅作回退。
    """
    from config import search_keywords, start_urls

    if keywords is None:
        keywords = search_keywords()

    for start_url in start_urls():
        discovery_run = await _discover_pages(start_url, keywords)

        from discovery.urltools import normalize_candidate_url

        meta = {}
        for candidate in discovery_run.candidates:
            key = normalize_candidate_url(candidate.url) or candidate.url
            meta[key] = candidate

        for page in discovery_run.pages:
            key = normalize_candidate_url(page.url) or page.url
            candidate = meta.get(key)
            title = (
                candidate.title_hint
                if candidate is not None and candidate.title_hint
                else _page_title(page)
            )
            date = (
                candidate.published_date or ""
                if candidate is not None
                else ""
            )
            yield page.url, page.html, title, date
