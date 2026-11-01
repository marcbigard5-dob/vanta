"""Catalogue loading and Markdown link extraction."""
from __future__ import annotations
import json
import re
from pathlib import Path
from urllib.parse import urlparse

LINK_RE = re.compile(r"!?\[[^\]]*\]\((https?://[^\s)]+)(?:\s+[^)]*)?\)", re.I)
# Capture bare HTTP(S) links too, not only GitHub links. Markdown links are
# also found by LINK_RE; the final de-duplication keeps each URL once.
BARE_URL_RE = re.compile(r"https?://[^\s<>\"'()]+", re.I)

def load_sources(path: str | Path | None = None) -> list[dict]:
    if path is not None:
        source_path = Path(path)
    else:
        project_file = Path(__file__).resolve().parents[2] / "config" / "sources.json"
        packaged_file = Path(__file__).resolve().parent / "sources.json"
        source_path = project_file if project_file.exists() else packaged_file
    data = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("Source configuration must be a JSON array of objects")
    return data

def extract_links(markdown: str) -> list[str]:
    found = LINK_RE.findall(markdown) + BARE_URL_RE.findall(markdown)
    result, seen = [], set()
    for raw in found:
        url = raw.rstrip(".,;:!?")
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
    owner, repo = parts[0], parts[1].removesuffix(".git")
    if not owner or not repo:
        return None
    return f"{owner}/{repo}"
