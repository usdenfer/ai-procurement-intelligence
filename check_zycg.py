"""zycg 限流后验证脚本：低频单次探测，确认 WAF 冷却后能否抓到公告。"""
import asyncio
import time

import _bootstrap
_bootstrap.ensure_wkc()

from crawler import crawl
from discovery import discover_pages
from discovery.models import BudgetManager

ZYC = "https://www.zycg.gov.cn/"


async def main():
    started = time.monotonic()
    try:
        base = await crawl(ZYC, depth=1, render=False)
    except Exception as exc:
        print("crawl failed:", type(exc).__name__, exc)
        return
    print("base pages:", len(base.pages))
    budget = BudgetManager(timeout_seconds=150, started_at=started)
    run = await discover_pages(ZYC, ["大学"], base, 1, "auto", budget=budget)
    print("pages:", len(run.pages))
    print("sources_succeeded:", sorted(run.stats.sources_succeeded))
    print("warnings:", run.stats.warnings)
    for p in run.pages[:5]:
        print("  -", p.url[:90])


asyncio.run(main())
