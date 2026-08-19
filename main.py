"""Command-line entrypoint: ingest, ask."""
from __future__ import annotations

import argparse
import asyncio

import _bootstrap
_bootstrap.ensure_wkc()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-procurement-intelligence")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest", help="抓取云南政府采购网公告并入库")
    ask_p = sub.add_parser("ask", help="基于知识库问答")
    ask_p.add_argument("question", help="要提问的内容")
    return parser


async def _ask(question: str) -> None:
    from ask import ask
    from store import Store

    store = Store()
    result = await ask(question, store)
    print(result["answer"])
    for src in result["sources"]:
        print(f"- {src}")


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "ask":
        asyncio.run(_ask(args.question))
    elif args.command == "ingest":
        from ingest import ingest
        from source import yngp_pages
        from store import Store

        counts = asyncio.run(ingest(yngp_pages(), Store()))
        print(counts)


if __name__ == "__main__":
    main()
