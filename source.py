"""Yield crawled procurement pages from the reused web_keyword_catcher crawler."""
from __future__ import annotations

from collections.abc import AsyncIterator

from bs4 import BeautifulSoup

YNGP_START = "http://www.yngp.com/"


def _page_title(page) -> str:
    soup = BeautifulSoup(page.html, "html.parser")
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return ""


async def yngp_pages(
    keywords: list[str] | None = None,
) -> AsyncIterator[tuple[str, str, str, str]]:
    """Yield (url, html, title, published_date) for yngp procurement notices.

    yngp.com 的公告列表由 bootgrid AJAX 接口驱动，静态 HTML 里没有文章
    链接，因此不能走裸 BFS 归档深扫。这里走 discovery 引擎 + YngpAdapter：
    先用静态 BFS 抓首页建立 base_result（用于识别站点适配器），再让
    YngpProvider 用给定关键词查询 JSON 列表接口，最后静态抓取详情正文。

    标题与发布日期取自接口返回的 bulletintitle / finishday（挂在
    Candidate.title_hint / published_date 上），详情页 <title> 仅作回退。
    """
    import _bootstrap
    _bootstrap.ensure_wkc()

    from crawler import crawl  # noqa: E402
    from discovery import discover_pages  # noqa: E402
    from discovery.urltools import normalize_candidate_url  # noqa: E402

    from config import query_types, search_keywords  # noqa: E402

    if keywords is None:
        keywords = search_keywords()
    base_result = await crawl(YNGP_START, depth=1, render=False)
    discovery_run = await discover_pages(
        YNGP_START, keywords, base_result, 1, "auto",
        query_types=query_types(),
    )

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
