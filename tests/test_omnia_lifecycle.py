"""End-to-end OMNIA lifecycle test: plan -> approve -> coordinate -> execute -> audit."""
import tempfile
import unittest
from pathlib import Path

from osihub.agent.capabilities import CapabilityRegistry
from osihub.agent.coordinator import MultiAgentCoordinator
from osihub.agent.engine import ExecutionEngine
from osihub.agent.model_router import ModelRouter
from osihub.agent.orchestrator import Orchestrator
from osihub.agent.policy import ApprovalLedger
from osihub.agent.runtime import AgentRuntime
from osihub.agent.store import TaskStore


class PlanningProvider:
    name = "test-planner"

    def plan(self, prompt):
        return [
            {"title": "Research source material", "description": prompt, "risk": "high"},
            {"title": "Analyze the findings", "description": "Summarize verified inputs", "risk": "low"},
        ]


class ReasoningProvider:
    name = "test-local"

    def __init__(self):
        self.calls = []

    def generate(self, messages, *, task_class="general", json_mode=False):
        self.calls.append(task_class)
        return ('{"findings":"bounded test result","limitations":["not independently verified"],'
                '"next_dependencies":[]}'), "test-local"


class OmniLifecycleTests(unittest.TestCase):
    def test_complete_supervised_lifecycle_and_audit_trail(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "omnia.sqlite3")
            store = TaskStore(db)
            planner = Orchestrator(store, PlanningProvider())
            provider = ReasoningProvider()
            router = ModelRouter({"local": provider}, default="local")
            coordinator = MultiAgentCoordinator(store, router)
            registry = CapabilityRegistry(db)
            approvals = ApprovalLedger(db)
            runtime = AgentRuntime(registry)
            engine = ExecutionEngine(registry, approvals, runtime, db)

            task = planner.create_task("Research and analyze a sample data request")
            planned = planner.plan_task(task["id"])
            self.assertEqual(planned["status"], "awaiting_approval")
            self.assertTrue(planned["approval_required"])

            # A task-level approval is required before any specialist starts.
            blocked_before_approval = False
            try:
                coordinator.start(task["id"])
            except Exception:
                blocked_before_approval = True
            self.assertTrue(blocked_before_approval)
            approved_task = store.approve(task["id"])
            self.assertEqual(approved_task["status"], "approved")

            run = coordinator.start(task["id"])
            self.assertEqual(run["status"], "completed")
            self.assertEqual(len(run["steps"]), 2)
            self.assertEqual([call for call in provider.calls], ["research", "analysis"])
            self.assertFalse(run["verified"])
            self.assertTrue(all(step["status"] == "completed" for step in run["steps"]))

            manifest = {
                "id": "test.report", "name": "Test report writer",
                "description": "Deterministic in-process test capability",
                "source_url": "https://example.invalid/omnia-test",
                "source_version": "1.0",
                "input_schema": {"type": "object", "required": ["report"],
                                 "properties": {"report": {"type": "string", "maxLength": 200}},
                                 "additionalProperties": False},
                "output_schema": {"type": "object", "required": ["stored"],
                                  "properties": {"stored": {"type": "boolean"}}},
                "risk": "medium", "permissions": [],
            }
            registry.register(manifest)
            registry.set_enabled("test.report", True, reviewed=True)
            runtime.register_handler("test.report", lambda args: {"stored": bool(args["report"])})
            args = {"report": "test lifecycle result"}
            approval = approvals.request("test.report", "local", args, [], "1.0", "medium")
            approvals.decide(approval["approval_id"], True, approval["digest"])
            execution = engine.execute("test.report", args, approval_id=approval["approval_id"])
            self.assertEqual(execution["status"], "completed")
            self.assertEqual(execution["result"], {"stored": True})
            self.assertFalse(execution["verified"])
            self.assertEqual(engine.get_execution(execution["execution_id"])["status"], "completed")

            # Approval is bound to one exact execution and cannot be replayed.
            with self.assertRaises(Exception):
                engine.execute("test.report", args, approval_id=approval["approval_id"])

            persisted_task = store.get(task["id"])
            persisted_run = coordinator.get_run(run["id"])
            self.assertEqual(persisted_task["status"], "approved")
            self.assertEqual(persisted_run["status"], "completed")
            self.assertGreaterEqual(len(persisted_run["events"]), 6)


if __name__ == "__main__":
    unittest.main()
