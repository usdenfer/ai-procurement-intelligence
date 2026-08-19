"""Command-line entrypoint: ingest, ask, schedule."""
from __future__ import annotations

import argparse
import asyncio
import time

import _bootstrap
_bootstrap.ensure_wkc()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-procurement-intelligence")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="抓取采购公告并入库")
    ask_p = sub.add_parser("ask", help="基于知识库问答")
    ask_p.add_argument("question", help="要提问的内容")
    sched_p = sub.add_parser("schedule", help="按固定间隔反复入库（增量）")
    sched_p.add_argument("--interval-hours", type=float, default=None,
                         help="入库间隔（小时），默认读 AI_PROC_INTERVAL_HOURS")
    return parser


async def _ask(question: str) -> None:
    from ask import ask
    from store import Store

    store = Store()
    result = await ask(question, store)
    print(result["answer"])
    for src in result["sources"]:
        print(f"- {src}")


async def _ingest_once() -> dict:
    from ingest import ingest
    from source import pages
    from store import Store

    return await ingest(pages(), Store())


def _interval_hours(flag: float | None) -> float:
    import os

    if flag is not None and flag > 0:
        return flag
    raw = os.environ.get("AI_PROC_INTERVAL_HOURS", "24")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = 24.0
    return value if value > 0 else 24.0


def _schedule(interval_hours: float) -> None:
    print(f"每 {interval_hours} 小时入库一次，Ctrl+C 停止")
    while True:
        counts = asyncio.run(_ingest_once())
        print(counts)
        time.sleep(interval_hours * 3600)


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "ask":
        asyncio.run(_ask(args.question))
    elif args.command == "ingest":
        print(asyncio.run(_ingest_once()))
    elif args.command == "schedule":
        _schedule(_interval_hours(args.interval_hours))


if __name__ == "__main__":
    main()
