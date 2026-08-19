"""FastAPI web UI for the AI procurement intelligence knowledge base."""
from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import schedule_enabled, schedule_time

STATIC_DIR = Path(__file__).resolve().parent / "static"

_ingest_state: dict = {
    "status": "idle",
    "counts": None,
    "error": None,
    "phase": None,
    "candidates_found": None,
    "documents": 0,
    "chunks": 0,
    "errors": 0,
}


def _progress_cb(update: dict) -> None:
    _ingest_state.update(update)


async def _run_ingest() -> None:
    from ingest import ingest
    from source import pages
    from store import Store

    _ingest_state.update(
        status="running", counts=None, error=None,
        phase=None, candidates_found=None,
        documents=0, chunks=0, errors=0,
    )
    try:
        counts = await ingest(
            pages(on_progress=_progress_cb),
            Store(),
            on_progress=_progress_cb,
        )
        _ingest_state.update(status="done", counts=counts)
    except Exception as exc:  # noqa: BLE001
        _ingest_state.update(status="error", error=str(exc))


async def _scheduler_loop() -> None:
    from datetime import datetime, timedelta

    hour, minute = schedule_time()
    while True:
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())
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
