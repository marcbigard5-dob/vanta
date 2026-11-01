"""Synchronise configured upstream README catalogues."""
from __future__ import annotations
import urllib.request
from .catalog import load_sources, extract_links, classify_url, github_slug
from .github import GitHubClient
from .db import Store

RAW = "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

def fetch_text(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent":"OpenSource-Intelligence-Hub/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")

def sync(store: Store, client: GitHubClient, sources_path=None, metadata_limit: int = 100) -> tuple[int, list[str]]:
    """Index catalogue links; enrich at most metadata_limit GitHub repos per run."""
    if metadata_limit < 0:
        raise ValueError("metadata_limit must be zero or greater")
    added, errors, enriched = 0, [], 0
    for source in load_sources(sources_path):
        markdown = None
        for branch in ("main", "master"):
            try:
                markdown = fetch_text(RAW.format(owner=source["owner"], repo=source["repo"], branch=branch, path=source["readme"]))
                break
            except Exception:
                continue
        if markdown is None:
            errors.append(f"{source['name']}: README could not be fetched from main or master")
            continue
        for link in extract_links(markdown):
            slug = github_slug(link)
            meta = {}
            if slug and enriched < metadata_limit:
                try:
                    meta = client.repository(slug)
                    enriched += 1
                except Exception as exc:
                    errors.append(f"{slug}: {exc}")
                    enriched += 1
            store.upsert({"url":link,"source":source["name"],"kind":"repository" if slug else classify_url(link),
                "slug":slug,"title":slug or link,"description":meta.get("description",""),
                "stars":meta.get("stars"),"language":meta.get("language",""),"license":meta.get("license",""),
                "archived":int(meta.get("archived",False)) if meta else None,"pushed_at":meta.get("pushed_at","")})
            added += 1
    return added, errors
