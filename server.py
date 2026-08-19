"""FastAPI web UI for the AI procurement intelligence knowledge base."""
from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

import _bootstrap
_bootstrap.ensure_wkc()

from config import interval_hours, schedule_enabled  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"

_ingest_state: dict = {"status": "idle", "counts": None, "error": None}


async def _run_ingest() -> None:
    from ingest import ingest
    from source import pages
    from store import Store

    _ingest_state.update(status="running", counts=None, error=None)
    try:
        counts = await ingest(pages(), Store())
        _ingest_state.update(status="done", counts=counts)
    except Exception as exc:  # noqa: BLE001
        _ingest_state.update(status="error", error=str(exc))


async def _scheduler_loop() -> None:
    while True:
        await asyncio.sleep(interval_hours() * 3600)
        if _ingest_state["status"] != "running":
            await _run_ingest()


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    scheduler_task = None
    if schedule_enabled():
        scheduler_task = asyncio.create_task(_scheduler_loop())
    yield
    if scheduler_task is not None:
        scheduler_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await scheduler_task


app = FastAPI(title="AI 采购情报", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/stats")
async def stats() -> dict:
    from store import Store

    store = Store()
    row = store.conn.execute("SELECT COUNT(*) FROM documents").fetchone()
    return {"documents": row[0] if row else 0}


@app.post("/api/ingest")
async def start_ingest() -> dict:
    if _ingest_state["status"] == "running":
        return {"status": "running"}
    asyncio.create_task(_run_ingest())
    return {"status": "started"}


@app.get("/api/ingest/status")
async def ingest_status() -> dict:
    return _ingest_state


@app.post("/api/ask")
async def ask_endpoint(req: AskRequest) -> dict:
    from ask import ask
    from store import Store

    question = req.question.strip()
    if not question:
        return {"answer": "问题不能为空。", "sources": []}
    return await ask(question, Store())
