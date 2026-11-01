"""First-stage task planning and approval policy."""
from __future__ import annotations
from .providers import OllamaProvider
from .store import TaskStore


class Orchestrator:
    def __init__(self, store: TaskStore, provider=None):
        self.store = store
        self.provider = provider or OllamaProvider()

    def create_task(self, prompt: str) -> dict:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Prompt must not be empty")
        if len(prompt) > 12000:
            raise ValueError("Prompt exceeds 12000 characters")
        return self.store.create(prompt)

    def plan_task(self, task_id: str) -> dict:
        task = self.store.get(task_id)
        if task is None:
            raise KeyError(task_id)
        if task["status"] not in {"draft", "failed"}:
            raise ValueError(f"Task cannot be planned from status {task['status']}")
        try:
            plan = self.provider.plan(task["prompt"])
        except Exception as exc:
            self.store.set_status(task_id, "failed", str(exc)[:1000])
            raise
        approval_required = any(step["risk"] in {"medium", "high"} for step in plan)
        return self.store.update_plan(task_id, plan, self.provider.name, approval_required)
