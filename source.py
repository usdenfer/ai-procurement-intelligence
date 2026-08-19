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


async def yngp_pages() -> AsyncIterator[tuple[str, str, str, str]]:
    """Yield (url, html, title, published_date) for yngp procurement notices.

    Thin adapter over the reused crawler's archive deep-scan, which renders
    category lists (full pagination) and statically fetches every article body.
    """
    import _bootstrap
    _bootstrap.ensure_wkc()

    from crawler import crawl_archive  # noqa: E402

    result = await crawl_archive(YNGP_START)
    for page in result.pages:
        yield page.url, page.html, _page_title(page), ""
