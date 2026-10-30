"""Small standard-library GitHub REST client."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request

API = "https://api.github.com"

class GitHubClient:
    def __init__(self, token: str | None = None, timeout: int = 20):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.timeout = timeout

    def get_json(self, url: str) -> dict:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "OpenSource-Intelligence-Hub/0.1"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"GitHub API returned HTTP {exc.code} for {url}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Network error: {exc.reason}") from exc

    def repository(self, slug: str) -> dict:
        if slug.count("/") != 1:
            raise ValueError("Repository must be in owner/repo format")
        data = self.get_json(f"{API}/repos/{slug}")
        licence = data.get("license") or {}
        return {
            "slug": data.get("full_name", slug),
            "description": data.get("description") or "",
            "stars": int(data.get("stargazers_count") or 0),
            "language": data.get("language") or "",
            "license": licence.get("spdx_id") or "Unknown",
            "archived": bool(data.get("archived")),
            "pushed_at": data.get("pushed_at") or "",
            "html_url": data.get("html_url") or f"https://github.com/{slug}",
        }
