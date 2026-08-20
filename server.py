"""FastAPI web UI for the AI procurement intelligence knowledge base."""
from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import schedule_enabled as _cfg_schedule_enabled
from config import schedule_time as _cfg_schedule_time
from config import end_date as _cfg_end_date
from config import start_date as _cfg_start_date
from config import ask_top_k as _cfg_ask_top_k
from config import max_tokens as _cfg_max_tokens

import settings_store

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


def _default_settings() -> dict:
    hour, minute = _cfg_schedule_time()
    return {
        "keywords": [],
        "start_urls": [],
        "schedule_enabled": _cfg_schedule_enabled(),
        "schedule_time": f"{hour:02d}:{minute:02d}",
        "start_date": _cfg_start_date(),
        "end_date": _cfg_end_date(),
        "top_k": _cfg_ask_top_k(),
        "max_tokens": _cfg_max_tokens(),
    }


_settings: dict = settings_store.load(_default_settings())


def _parse_time(value: str) -> tuple[int, int]:
    try:
        hour, minute = (int(part) for part in value.split(":"))
    except (ValueError, TypeError):
        return 17, 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return 17, 0
    return hour, minute


def _next_run() -> str:
    hour, minute = _parse_time(_settings["schedule_time"])
    now = datetime.now()
    nxt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if nxt <= now:
        nxt += timedelta(days=1)
    return nxt.strftime("%Y-%m-%d %H:%M:%S")


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
            pages(
                keywords=_settings["keywords"] or None,
                start_urls=_settings["start_urls"] or None,
                start_date=_settings.get("start_date") or None,
                end_date=_settings.get("end_date") or None,
                on_progress=_progress_cb,
            ),
            Store(),
            on_progress=_progress_cb,
        )
        _ingest_state.update(status="done", counts=counts)
    except Exception as exc:  # noqa: BLE001
        _ingest_state.update(status="error", error=str(exc))


async def _scheduler_loop() -> None:
    while True:
        if not _settings["schedule_enabled"]:
            await asyncio.sleep(30)
            continue
        hour, minute = _parse_time(_settings["schedule_time"])
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())
        if _ingest_state["status"] != "running":
            await _run_ingest()


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    scheduler_task = asyncio.create_task(_scheduler_loop())
    yield
    scheduler_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await scheduler_task


app = FastAPI(title="AI 采购情报", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    max_tokens: int | None = None


class SettingsUpdate(BaseModel):
    keywords: list[str] | None = None
    start_urls: list[str] | None = None
    schedule_enabled: bool | None = None
    schedule_time: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    top_k: int | None = None
    max_tokens: int | None = None


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/stats")
async def stats() -> dict:
    from store import Store

    store = Store()
    row = store.conn.execute("SELECT COUNT(*) FROM documents").fetchone()
    return {"documents": row[0] if row else 0}


@app.get("/api/settings")
async def get_settings() -> dict:
    return {**_settings, "next_run": _next_run()}


@app.post("/api/settings")
async def update_settings(req: SettingsUpdate) -> dict:
    if req.keywords is not None:
        _settings["keywords"] = [k.strip() for k in req.keywords if k.strip()]
    if req.start_urls is not None:
        _settings["start_urls"] = [
            u.strip() for u in req.start_urls if u.strip()
        ]
    if req.schedule_enabled is not None:
        _settings["schedule_enabled"] = req.schedule_enabled
    if req.schedule_time is not None:
        hour, minute = _parse_time(req.schedule_time)
        _settings["schedule_time"] = f"{hour:02d}:{minute:02d}"
    if req.start_date is not None:
        _settings["start_date"] = req.start_date.strip()
    if req.end_date is not None:
        _settings["end_date"] = req.end_date.strip()
    if req.top_k is not None and req.top_k > 0:
        _settings["top_k"] = req.top_k
    if req.max_tokens is not None and req.max_tokens > 0:
        _settings["max_tokens"] = req.max_tokens
    settings_store.save(_settings)
    return {**_settings, "next_run": _next_run()}


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
    top_k = req.top_k if req.top_k and req.top_k > 0 else _settings.get("top_k") or 40
    max_tokens = (
        req.max_tokens
        if req.max_tokens and req.max_tokens > 0
        else _settings.get("max_tokens") or 12000
    )
    return await ask(
        question,
        Store(),
        top_k=top_k,
        start_date=req.start_date or None,
        end_date=req.end_date or None,
        max_tokens=max_tokens,
    )
