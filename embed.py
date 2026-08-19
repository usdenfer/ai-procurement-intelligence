"""OpenAI-compatible embedding client."""
from __future__ import annotations

import httpx

from config import embedding_api_key, embedding_base_url, embedding_model


class EmbedError(Exception):
    pass


async def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if not embedding_api_key():
        raise EmbedError("未配置 embedding API key")
    payload = {"model": embedding_model(), "input": texts}
    client = httpx.AsyncClient(timeout=60.0)
    try:
        resp = await client.post(
            f"{embedding_base_url()}/embeddings",
            json=payload,
            headers={"Authorization": f"Bearer {embedding_api_key()}"},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        return [item["embedding"] for item in data]
    except httpx.HTTPError as exc:
        raise EmbedError(f"embedding 请求失败: {exc}") from exc
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise EmbedError("embedding 返回格式异常") from exc
    finally:
        await client.aclose()
