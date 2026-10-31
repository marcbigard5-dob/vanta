"""Provider-neutral planning interface with an Ollama implementation."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request


class ProviderError(RuntimeError):
    pass


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: int = 90):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.timeout = timeout

    def plan(self, prompt: str) -> list[dict]:
        system = (
            "You are the planning component of OMNIA. Convert the user's request into a safe, concise plan. "
            "Return ONLY valid JSON: {\"steps\":[{\"title\":string,\"description\":string,"
            "\"risk\":\"low\"|\"medium\"|\"high\"}]}. Use 1-8 steps. "
            "Do not claim tools were executed. Mark actions involving external side effects, credentials, "
            "payments, publishing, deletion, account changes, or sending messages as high risk."
        )
        body = json.dumps({"model": self.model, "stream": False, "format": "json",
                           "messages": [{"role": "system", "content": system},
                                        {"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(self.base_url + "/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload.get("message", {}).get("content", "")
            parsed = json.loads(content)
            steps = parsed.get("steps") if isinstance(parsed, dict) else None
            if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
                raise ProviderError("Model returned an invalid plan shape")
            clean = []
            for step in steps:
                if not isinstance(step, dict) or not str(step.get("title", "")).strip():
                    raise ProviderError("Model returned an invalid plan step")
                risk = step.get("risk", "medium")
                if risk not in {"low", "medium", "high"}:
                    risk = "high"
                clean.append({"title": str(step["title"])[:160],
                              "description": str(step.get("description", ""))[:1200], "risk": risk})
            return clean
        except urllib.error.URLError as exc:
            raise ProviderError(f"Ollama is not reachable at {self.base_url}: {exc}") from exc
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ProviderError(f"Ollama returned an unreadable response: {exc}") from exc
