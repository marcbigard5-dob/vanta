"""FastAPI entry point for the OMNIA task-planning foundation."""
from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .agent.orchestrator import Orchestrator
from .agent.providers import ProviderError
from .agent.store import TaskStore

store = TaskStore()
agent = Orchestrator(store)
app = FastAPI(title="OMNIA Agent API", version="0.2.0",
              description="Supervised AI task planning foundation. Tool execution is not enabled yet.")


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)


@app.get("/health")
def health():
    return {"status": "ok", "service": "omnia-api", "execution_enabled": False,
            "model_provider": "ollama", "model": os.getenv("OLLAMA_MODEL", "llama3.2")}


@app.post("/api/tasks", status_code=201)
def create_task(body: TaskRequest):
    try:
        return agent.create_task(body.prompt)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/tasks")
def list_tasks(limit: int = 50):
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    return {"tasks": store.list(limit)}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks/{task_id}/plan")
def plan_task(task_id: str):
    try:
        return agent.plan_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/tasks/{task_id}/approve")
def approve_task(task_id: str):
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] != "awaiting_approval" or not task["approval_required"]:
        raise HTTPException(status_code=409, detail="Task is not awaiting approval")
    return store.approve(task_id)


def run():
    import uvicorn
    uvicorn.run("osihub.api:app", host=os.getenv("OMNIA_HOST", "127.0.0.1"),
                port=int(os.getenv("OMNIA_PORT", "8000")), reload=False)
