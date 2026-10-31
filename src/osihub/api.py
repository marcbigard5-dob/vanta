"""FastAPI entry point for the OMNIA supervised planning foundation."""
from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .agent.orchestrator import Orchestrator
from .agent.providers import ProviderError
from .agent.store import TaskStore
from .agent.capabilities import CapabilityError, CapabilityRegistry
from .agent.policy import ApprovalError, ApprovalLedger
from .agent.model_router import ModelRouter
from .agent.providers import OllamaProvider
from .agent.runtime import AgentRuntime\nfrom .agent.coordinator import MultiAgentCoordinator, CoordinationError

store = TaskStore()
model_router = ModelRouter.from_env()
agent = Orchestrator(store, OllamaProvider(router=model_router))
capabilities = CapabilityRegistry(store.path)
approvals = ApprovalLedger(store.path)
runtime = AgentRuntime(capabilities)\ncoordinator = MultiAgentCoordinator(store, model_router)
app = FastAPI(title="OMNIA Agent API", version="0.3.0",
              description="Supervised planning and default-deny capability registry. Tool execution is disabled.")


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)


class CapabilityManifest(BaseModel):
    id: str
    name: str
    description: str
    source_url: str
    source_version: str
    input_schema: dict
    output_schema: dict
    risk: str
    permissions: list[str]


class CapabilityEnableRequest(BaseModel):
    reviewed: bool = False


class ApprovalRequest(BaseModel):
    capability_id: str
    target: str
    arguments: dict
    permissions: list[str]
    capability_version: str
    risk: str


class ApprovalDecision(BaseModel):
    approved: bool
    expected_digest: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "omnia-api", "execution_enabled": False,
            "capability_registry": True, "model_providers": model_router.inventory(),
            "execution_enabled": False}


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


@app.get("/api/models")
def list_models():
    return {"providers": model_router.inventory(), "routing": "explicit-task-class",
            "default_provider": model_router.default}


@app.get("/api/capabilities")
def list_capabilities(limit: int = 100):
    if not 1 <= limit <= 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    return {"capabilities": capabilities.list(limit), "execution_enabled": False}


@app.post("/api/capabilities", status_code=201)
def register_capability(body: CapabilityManifest):
    try:
        return capabilities.register(body.model_dump())
    except CapabilityError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/capabilities/{capability_id}/enable")
def enable_capability(capability_id: str, body: CapabilityEnableRequest):
    try:
        item = capabilities.set_enabled(capability_id, True, reviewed=body.reviewed)
    except CapabilityError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    return item


@app.post("/api/capabilities/{capability_id}/disable")
def disable_capability(capability_id: str):
    item = capabilities.set_enabled(capability_id, False)
    if item is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    return item


@app.post("/api/approvals", status_code=201)
def request_action_approval(body: ApprovalRequest):
    capability = capabilities.get(body.capability_id)
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    if not capability["enabled"] or not capability["reviewed"]:
        raise HTTPException(status_code=409, detail="Capability is disabled or not reviewed")
    if not set(body.permissions).issubset(set(capability["permissions"])):
        raise HTTPException(status_code=403, detail="Requested permissions exceed capability manifest")
    try:
        return approvals.request(body.capability_id, body.target, body.arguments,
                                 body.permissions, body.capability_version, body.risk)
    except ApprovalError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/approvals/{approval_id}/decision")
def decide_action_approval(approval_id: str, body: ApprovalDecision):
    try:
        item = approvals.decide(approval_id, body.approved, body.expected_digest)
    except ApprovalError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return item


def run():
    import uvicorn
    uvicorn.run("osihub.api:app", host=os.getenv("OMNIA_HOST", "127.0.0.1"),
                port=int(os.getenv("OMNIA_PORT", "8000")), reload=False)
