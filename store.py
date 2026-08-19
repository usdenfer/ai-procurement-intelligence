"""Persistence: SQLite for raw documents, Chroma for vectors."""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import chromadb

from chunk import Chunk
from config import data_dir


def _doc_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, root: str | None = None, chroma_client=None):
        root = root or data_dir()
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.root / "documents.db")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS documents ("
            " id TEXT PRIMARY KEY, url TEXT NOT NULL, title TEXT,"
            " published_date TEXT, district TEXT DEFAULT '',"
            " clean_text TEXT NOT NULL, ingested_at TEXT NOT NULL)"
        )
        columns = [
            row[1]
            for row in self.conn.execute("PRAGMA table_info(documents)")
        ]
        if "district" not in columns:
            self.conn.execute(
                "ALTER TABLE documents ADD COLUMN district TEXT DEFAULT ''"
            )
        self.chroma = chroma_client or chromadb.PersistentClient(
            path=str(self.root / "chroma")
        )
        self.collection = self.chroma.get_or_create_collection(
            "yngp_procurements", embedding_function=None
        )

    def save_document(
        self,
        url: str,
        clean_text: str,
        title: str,
        published_date: str,
        district: str = "",
    ) -> str:
        doc_id = _doc_id(url)
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO documents"
            "(id, url, title, published_date, district, clean_text, ingested_at)"
            " VALUES(?,?,?,?,?,?,?)"
            " ON CONFLICT(id) DO UPDATE SET"
            " clean_text=excluded.clean_text,"
            " title=excluded.title,"
            " published_date=excluded.published_date,"
            " district=excluded.district,"
            " ingested_at=excluded.ingested_at",
            (doc_id, url, title, published_date, district, clean_text, now),
        )
        self.conn.commit()
        return doc_id

    def upsert_chunks(
        self, doc_id: str, chunks: list[Chunk], vectors: list[list[float]]
    ) -> None:
        if not chunks:
            return
        self.collection.upsert(
            ids=[f"{doc_id}:{c.index}" for c in chunks],
            embeddings=vectors,
            documents=[c.text for c in chunks],
            metadatas=[c.metadata() for c in chunks],
        )

    def query(self, vector: list[float], top_k: int) -> list[dict]:
        result = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        docs = result.get("documents") or [[]]
        metas = result.get("metadatas") or [[]]
        out: list[dict] = []
        for doc, meta in zip(docs[0], metas[0]):
            out.append({
                "text": doc,
                "url": (meta or {}).get("url", ""),
                "district": (meta or {}).get("district", ""),
            })
        return out
