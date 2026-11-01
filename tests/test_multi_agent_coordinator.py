import tempfile
import unittest
from pathlib import Path

from osihub.agent.coordinator import MultiAgentCoordinator, CoordinationError, select_agent
from osihub.agent.model_router import ModelRouter
from osihub.agent.store import TaskStore


class FakeProvider:
    name = "fake-local"
    def __init__(self):
        self.calls = []
    def generate(self, messages, *, json_mode=False):
        self.calls.append(messages)
        return "Result: bounded analysis. No external action performed."


class MultiAgentCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = TaskStore(Path(self.tmp.name) / "omnia.sqlite3")
        self.provider = FakeProvider()
        self.router = ModelRouter({"local": self.provider}, default="local")
        self.coordinator = MultiAgentCoordinator(self.store, self.router)

    def tearDown(self):
        self.tmp.cleanup()

    def test_specialist_routing(self):
        self.assertEqual(select_agent("Research sources", ""), "research")
        self.assertEqual(select_agent("Implement API", ""), "coding")
        self.assertEqual(select_agent("Analyze results", ""), "analysis")
        self.assertEqual(select_agent("Design interface", ""), "design")

    def test_run_persists_ordered_steps_and_events(self):
        task = self.store.create("Build and analyze a product")
        task = self.store.update_plan(task["id"], [
            {"title": "Research sources", "description": "Find context", "risk": "low"},
            {"title": "Analyze findings", "description": "Compare options", "risk": "low"},
            {"title": "Design interface", "description": "Propose UX", "risk": "low"}],
            "fake", False)
        result = self.coordinator.start(task["id"])
        self.assertEqual(result["status"], "completed")
        self.assertEqual([s["agent"] for s in result["steps"]], ["research", "analysis", "design"])
        self.assertEqual(len(self.provider.calls), 3)
        self.assertGreaterEqual(len(result["events"]), 8)
        self.assertFalse(result["verified"])
        self.assertTrue(all(not s["verified"] for s in result["steps"]))

    def test_awaiting_approval_task_is_blocked(self):
        task = self.store.create("Do something external")
        self.store.update_plan(task["id"], [
            {"title": "Publish report", "description": "External side effect", "risk": "high"}],
            "fake", True)
        with self.assertRaises(CoordinationError):
            self.coordinator.start(task["id"])
        self.assertEqual(len(self.provider.calls), 0)

    def test_unknown_run(self):
        with self.assertRaises(KeyError):
            self.coordinator.get_run("missing")


if __name__ == "__main__":
    unittest.main()
