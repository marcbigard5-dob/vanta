"""SQLite cache for discovered catalogue entries."""
from __future__ import annotations
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
 url TEXT PRIMARY KEY, source TEXT NOT NULL, kind TEXT NOT NULL,
 slug TEXT, title TEXT NOT NULL, description TEXT DEFAULT '',
 stars INTEGER, language TEXT DEFAULT '', license TEXT DEFAULT '',
 archived INTEGER, pushed_at TEXT DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""
class Store:
    def __init__(self, path: str | Path = "osihub.sqlite3"):
        self.path = str(path)
        with self.connect() as db:
            db.executescript(SCHEMA)

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def upsert(self, item: dict) -> None:
        fields = ("url","source","kind","slug","title","description","stars","language","license","archived","pushed_at")
        values = [item.get(k) for k in fields]
        with self.connect() as db:
            db.execute("""INSERT INTO entries(url,source,kind,slug,title,description,stars,language,license,archived,pushed_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET
            source=excluded.source,kind=excluded.kind,slug=excluded.slug,title=excluded.title,
            description=excluded.description,stars=excluded.stars,language=excluded.language,
            license=excluded.license,archived=excluded.archived,pushed_at=excluded.pushed_at,
            updated_at=CURRENT_TIMESTAMP""", values)

    def search(self, query: str = "", kind: str | None = None, limit: int = 50) -> list[dict]:
        sql = "SELECT * FROM entries WHERE (lower(title) LIKE ? OR lower(url) LIKE ? OR lower(description) LIKE ?)"
        term = f"%{query.lower()}%"
        args: list = [term, term, term]
        if kind:
            sql += " AND kind=?"
            args.append(kind)
        sql += " ORDER BY COALESCE(stars,0) DESC, title COLLATE NOCASE LIMIT ?"
        args.append(limit)
        with self.connect() as db:
            return [dict(row) for row in db.execute(sql, args).fetchall()]

    def count(self) -> int:
        with self.connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM entries").fetchone()[0])
