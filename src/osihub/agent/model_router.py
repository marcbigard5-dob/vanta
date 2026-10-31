"""Provider-neutral model routing for local Ollama and optional OpenAI-compatible APIs."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class ModelError(RuntimeError):
    pass


class ModelProvider(Protocol):
    name: str
    def generate(self, messages: list[dict], *, json_mode: bool = False) -> str: ...


@dataclass
class ModelConfig:
    name: str
    base_url: str
    model: str
    api_key_env: str = ""
    timeout: int = 90


class OllamaModelProvider:
    def __init__(self, config: ModelConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    def generate(self, messages: list[dict], *, json_mode: bool = False) -> str:
        body = {"model": self.config.model, "stream": False, "messages": messages}
        if json_mode:
            body["format"] = "json"
        return self._post("/api/chat", body, None, "message.content")

    def _request(self, url: str, body: dict | None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            if not isinstance(result, dict):
                raise ModelError("Ollama returned a non-object response")
            return result
        except urllib.error.HTTPError as exc:
            raise ModelError(f"Ollama HTTP error {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ModelError("Ollama is unreachable") from exc
        except json.JSONDecodeError as exc:
            raise ModelError("Ollama returned invalid JSON") from exc

    def _post(self, path: str, body: dict, key: str | None, field: str) -> str:
        payload = self._request(self.config.base_url.rstrip("/") + path, body)
        try:
            value = payload
            for part in field.split("."):
                value = value[int(part)] if part.isdigit() else value[part]
            if not isinstance(value, str) or not value.strip():
                raise ValueError("empty model response")
            return value
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelError("Ollama returned an invalid response shape") from exc

    def list_models(self) -> list[str]:
        payload = self._request(self.config.base_url.rstrip("/") + "/api/tags", None)
        return sorted({m.get("name", "") for m in payload.get("models", []) if m.get("name")})


class OpenAICompatibleProvider:
    """Adapter for OpenAI-compatible chat-completions endpoints; opt-in via env config."""
    def __init__(self, config: ModelConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    def generate(self, messages: list[dict], *, json_mode: bool = False) -> str:
        body = {"model": self.config.model, "messages": messages, "stream": False}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        env_name = self.config.api_key_env
        key = os.getenv(env_name) if env_name else None
        return self._post("/chat/completions", body, key, "choices.0.message.content")

    def _post(self, path: str, body: dict, key: str | None, field: str) -> str:
        payload = self._request(self.config.base_url.rstrip("/") + path, body, key)
        try:
            value = payload
            for part in field.split("."):
                value = value[int(part)] if part.isdigit() else value[part]
            if not isinstance(value, str) or not value.strip():
                raise ValueError("empty model response")
            return value
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ModelError(f"{self.name} returned an invalid response shape") from exc

    def _request(self, url: str, body: dict | None, key: str | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + key
        request = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
            if not isinstance(result, dict):
                raise ModelError(f"{self.name} returned a non-object response")
            return result
        except urllib.error.HTTPError as exc:
            raise ModelError(f"{self.name} HTTP error {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ModelError(f"{self.name} is unreachable") from exc
        except json.JSONDecodeError as exc:
            raise ModelError(f"{self.name} returned invalid JSON") from exc


class ModelRouter:
    """Routes by explicit task class, with local-first and no silent provider fallback."""
    def __init__(self, providers: dict[str, ModelProvider], default: str = "ollama",
                 routes: dict[str, str] | None = None):
        if default not in providers:
            raise ValueError("Default model provider is not configured")
        self.providers = dict(providers)
        self.default = default
        self.routes = dict(routes or {})

    @classmethod
    def from_env(cls) -> "ModelRouter":
        local = ModelConfig("ollama", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
                            os.getenv("OLLAMA_MODEL", "llama3.2"),
                            timeout=int(os.getenv("OLLAMA_TIMEOUT", "90")))
        providers: dict[str, ModelProvider] = {"ollama": OllamaModelProvider(local)}
        # Remote provider is deliberately opt-in; secrets remain in environment variables.
        if os.getenv("OMNIA_OPENAI_BASE_URL") and os.getenv("OMNIA_OPENAI_MODEL"):
            cfg = ModelConfig("openai_compatible", os.environ["OMNIA_OPENAI_BASE_URL"],
                              os.environ["OMNIA_OPENAI_MODEL"],
                              os.getenv("OMNIA_OPENAI_API_KEY_ENV", "OMNIA_OPENAI_API_KEY"),
                              int(os.getenv("OMNIA_OPENAI_TIMEOUT", "90")))
            providers["openai_compatible"] = OpenAICompatibleProvider(cfg)
        return cls(providers, default=os.getenv("OMNIA_DEFAULT_PROVIDER", "ollama"))

    def provider_for(self, task_class: str = "general") -> ModelProvider:
        provider_name = self.routes.get(task_class, self.default)
        try:
            return self.providers[provider_name]
        except KeyError as exc:
            raise ModelError(f"No configured provider for task class: {task_class}") from exc

    def generate(self, messages: list[dict], *, task_class: str = "general",
                 json_mode: bool = False) -> tuple[str, str]:
        provider = self.provider_for(task_class)
        return provider.generate(messages, json_mode=json_mode), provider.name

    def inventory(self) -> list[dict]:
        return [{"name": name, "default": name == self.default,
                 "local": isinstance(provider, OllamaModelProvider)}
                for name, provider in self.providers.items()]
