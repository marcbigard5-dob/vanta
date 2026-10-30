"""Catalogue loading and Markdown link extraction."""
from __future__ import annotations
import json
import re
from pathlib import Path
from urllib.parse import urlparse

LINK_RE = re.compile(r"!?\[[^\]]*\]\((https?://[^\s)]+)(?:\s+[^)]*)?\)", re.I)
BARE_URL_RE = re.compile(r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", re.I)

def load_sources(path: str | Path | None = None) -> list[dict]:
    path = Path(path) if path else Path(__file__).resolve().parents[2] / "config" / "sources.json"
    return json.loads(path.read_text(encoding="utf-8"))

def extract_links(markdown: str) -> list[str]:
    found = LINK_RE.findall(markdown) + BARE_URL_RE.findall(markdown)
    result, seen = [], set()
    for raw in found:
        url = raw.rstrip(".,;")
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result

def classify_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host == "github.com" or host.endswith(".github.com"):
        return "repository"
    if host in {"rapidapi.com", "api-ninjas.com"}:
        return "api"
    return "resource"

def github_slug(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname not in {"github.com", "www.github.com"}:
        return None
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2 or parts[0] in {"topics", "collections", "marketplace", "orgs", "features"}:
        return None
    return f"{parts[0]}/{parts[1].removesuffix('.git')}"
