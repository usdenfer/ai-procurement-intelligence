"""Retrieve relevant chunks and answer with the reused DeepSeek client."""
from __future__ import annotations

import _bootstrap
_bootstrap.ensure_wkc()

from ai import chat  # noqa: E402

from embed import embed  # noqa: E402

_SYSTEM = (
    "你是采购公告问答助手。只根据给定的公告片段回答。"
    "如果问题要求列出/盘点/查询多个项目或公告，请逐条列出所有相关的公告"
    "（每条含名称、关键信息、地区、日期），不要遗漏、不要只挑其中几个。"
    "引用来源时附上片段对应的完整 URL。内容不足时明确说明，不要编造。"
)


def _build_user(question: str, hits: list[dict]) -> str:
    blocks = []
    for hit in hits:
        location = f"（{hit['district']}）" if hit.get("district") else ""
        blocks.append(f"来源：{hit['url']}{location}\n内容：{hit['text']}")
    context = "\n\n".join(blocks) if blocks else "（无相关公告片段）"
    return f"公告片段：\n{context}\n\n问题：{question}"


async def ask(
    question: str,
    store,
    top_k: int = 40,
    start_date: str | None = None,
    end_date: str | None = None,
    max_tokens: int = 12000,
) -> dict:
    vectors = await embed([question])
    hits = store.query(
        vectors[0], top_k=top_k, start_date=start_date, end_date=end_date
    )
    if not hits:
        return {"answer": "知识库中未找到相关内容。", "sources": []}
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": _build_user(question, hits)},
    ]
    answer = await chat(messages, max_tokens=max_tokens)
    sources = list(dict.fromkeys(h["url"] for h in hits if h["url"]))
    return {"answer": answer, "sources": sources}
