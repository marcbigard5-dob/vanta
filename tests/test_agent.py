import tempfile
import unittest
from pathlib import Path
from osihub.agent.orchestrator import Orchestrator
from osihub.agent.store import TaskStore


class FakeProvider:
    name = "fake"
    def __init__(self, plan=None):
        self.result = plan or [{"title": "Research options", "description": "Compare sources", "risk": "low"},
                               {"title": "Publish result", "description": "External side effect", "risk": "high"}]
    def plan(self, prompt):
        return self.result


class AgentFoundationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = TaskStore(Path(self.tmp.name) / "tasks.sqlite3")
        self.agent = Orchestrator(self.store, FakeProvider())

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_plan_task_requires_approval_for_high_risk(self):
        task = self.agent.create_task("Research and publish a report")
        self.assertEqual(task["status"], "draft")
        planned = self.agent.plan_task(task["id"])
        self.assertEqual(planned["status"], "awaiting_approval")
        self.assertTrue(planned["approval_required"])
        self.assertFalse(planned["approval_granted"])
        self.assertEqual(len(planned["plan"]), 2)

    def test_low_risk_plan_does_not_request_external_approval(self):
        provider = FakeProvider([{"title": "Summarize", "description": "Local only", "risk": "low"}])
        agent = Orchestrator(self.store, provider)
        task = agent.create_task("Summarize this text")
        planned = agent.plan_task(task["id"])
        self.assertEqual(planned["status"], "planned")
        self.assertFalse(planned["approval_required"])

    def test_empty_prompt_rejected(self):
        with self.assertRaises(ValueError):
            self.agent.create_task("   ")

    def test_unknown_task_rejected(self):
        with self.assertRaises(KeyError):
            self.agent.plan_task("missing")

    def test_approval_only_changes_waiting_task(self):
        task = self.agent.create_task("Research and publish")
        self.agent.plan_task(task["id"])
        approved = self.store.approve(task["id"])
        self.assertEqual(approved["status"], "approved")
        self.assertTrue(approved["approval_granted"])


if __name__ == "__main__":
    unittest.main()
