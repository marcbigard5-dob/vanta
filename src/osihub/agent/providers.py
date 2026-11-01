"""Planning adapter built on the shared model router."""
from __future__ import annotations
import json
from .model_router import ModelRouter, ModelError


class ProviderError(RuntimeError):
    pass


class OllamaProvider:
    """Backward-compatible planner; local Ollama remains the default route."""
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: int = 90,
                 router: ModelRouter | None = None):
        if router is not None:
            self.router = router
        elif base_url is None and model is None and timeout == 90:
            self.router = ModelRouter.from_env()
        else:
            # Preserve the old constructor for callers/tests while routing through one interface.
            import os
            from .model_router import ModelConfig, OllamaModelProvider
            cfg = ModelConfig("ollama", (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")),
                              model or os.getenv("OLLAMA_MODEL", "llama3.2"),
                              timeout=timeout)
            self.router = ModelRouter({"ollama": OllamaModelProvider(cfg)})

    def plan(self, prompt: str) -> list[dict]:
        system = (
            "You are OMNIA's planning component. Convert the user's request into a safe concise plan. "
            "Return ONLY JSON: {\"steps\":[{\"title\":string,\"description\":string,"
            "\"risk\":\"low\"|\"medium\"|\"high\"}]}. Use 1-8 steps. "
            "Never claim tools were executed. Mark external side effects, credentials, payments, "
            "publishing, deletion, account changes, or sending messages as high risk."
        )
        try:
            content, provider_name = self.router.generate(
                [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                task_class="planning", json_mode=True)
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
            self.name = provider_name
            return clean
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ProviderError("Model returned an unreadable planning response") from exc
        except ModelError as exc:
            raise ProviderError(str(exc)) from exc
