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

    from config import (  # noqa: E402
        full_sweep,
        max_windows,
        query_types,
        recent_days,
    )

    base_result = await crawl(start_url, depth=1, render=False)
    return await discover_pages(
        start_url, keywords, base_result, 1, "auto",
        query_types=query_types(),
        recent_days=recent_days(),
        max_windows_per_query=max_windows(),
        full_sweep=full_sweep(),
    )


async def pages(
    keywords: list[str] | None = None,
    on_progress=None,
    start_urls: list[str] | None = None,
) -> AsyncIterator[tuple[str, str, str, str, str]]:
    """Yield (url, html, title, published_date, district) across sources.

    走 discovery 引擎：先用静态 BFS 抓首页建立 base_result（用于识别站点
    适配器），再让适配器对应的 Provider 用给定关键词发现候选并抓取正文。
    标题/发布日期/地区取自候选元数据（Candidate.title_hint / published_date
    / district），详情页 <title> 仅作回退。
    on_progress(dict) 在发现前/后各回调一次，用于报告阶段与候选数。
    start_urls 为空或 None 时回退到配置默认。
    """
    from config import search_keywords
    from config import start_urls as default_start_urls

    if keywords is None:
        keywords = search_keywords()
    urls = list(start_urls) if start_urls else default_start_urls()

    for start_url in urls:
        if on_progress is not None:
            on_progress({"phase": "discovering", "candidates_found": 0})
        discovery_run = await _discover_pages(start_url, keywords)
        if on_progress is not None:
            on_progress({
                "phase": "ingesting",
                "candidates_found": discovery_run.stats.candidates_found,
            })

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
            district = (
                candidate.district or ""
                if candidate is not None
                else ""
            )
            yield page.url, page.html, title, date, district
