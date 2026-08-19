import asyncio
import json

import httpx
import pytest

import embed
from embed import EmbedError


def _run(coro):
    return asyncio.run(coro)


def _client_with(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_embed_returns_vectors_and_sends_payload(monkeypatch):
    monkeypatch.setenv("EMBEDDING_API_KEY", "sk-test")
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://x.test/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "m3")
    captured = {}

    def handler(request):
        captured["json"] = json.loads(request.content)
        captured["auth"] = request.headers["authorization"]
        return httpx.Response(
            200, json={"data": [{"embedding": [0.1, 0.2]},
                                {"embedding": [0.3, 0.4]}]}, request=request)

    async def run():
        async with _client_with(handler) as client:
            monkeypatch.setattr(embed.httpx, "AsyncClient", lambda *a, **k: client)
            return await embed.embed(["a", "b"])

    vectors = _run(run())
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["json"] == {"model": "m3", "input": ["a", "b"]}
    assert captured["auth"] == "Bearer sk-test"


def test_embed_empty_input_returns_empty():
    assert _run(embed.embed([])) == []


def test_embed_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(EmbedError):
        _run(embed.embed(["a"]))


def test_embed_raises_on_http_error(monkeypatch):
    monkeypatch.setenv("EMBEDDING_API_KEY", "sk-test")

    def handler(request):
        return httpx.Response(401, json={}, request=request)

    async def run():
        async with _client_with(handler) as client:
            monkeypatch.setattr(embed.httpx, "AsyncClient", lambda *a, **k: client)
            return await embed.embed(["a"])

    with pytest.raises(EmbedError):
        _run(run())


def test_embed_raises_on_malformed_response(monkeypatch):
    monkeypatch.setenv("EMBEDDING_API_KEY", "sk-test")

    def handler(request):
        return httpx.Response(200, json={"data": "bad"}, request=request)

    async def run():
        async with _client_with(handler) as client:
            monkeypatch.setattr(embed.httpx, "AsyncClient", lambda *a, **k: client)
            return await embed.embed(["a"])

    with pytest.raises(EmbedError):
        _run(run())
