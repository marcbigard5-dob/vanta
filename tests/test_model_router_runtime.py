import tempfile
import unittest
from pathlib import Path

from osihub.agent.model_router import ModelRouter, ModelError
from osihub.agent.capabilities import CapabilityRegistry
from osihub.agent.runtime import AgentRuntime, RuntimeErrorBase


class FakeProvider:
    name = "fake"
    def __init__(self, answer="ok"):
        self.answer = answer
    def generate(self, messages, *, json_mode=False):
        return self.answer


MANIFEST = {
    "id": "internal.echo", "name": "Echo", "description": "Test handler",
    "source_url": "https://example.invalid", "source_version": "1",
    "input_schema": {"type": "object"}, "output_schema": {"type": "object"},
    "risk": "low", "permissions": []
}


class ModelRouterRuntimeTests(unittest.TestCase):
    def test_router_uses_explicit_task_route(self):
        router = ModelRouter({"local": FakeProvider("local"), "remote": FakeProvider("remote")},
                             default="local", routes={"coding": "remote"})
        self.assertEqual(router.generate([], task_class="coding")[0], "remote")
        self.assertEqual(router.generate([])[0], "local")

    def test_unknown_route_fails_without_silent_fallback(self):
        router = ModelRouter({"local": FakeProvider()}, routes={"research": "missing"})
        with self.assertRaises(ModelError):
            router.generate([], task_class="research")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = CapabilityRegistry(Path(self.tmp.name) / "db.sqlite")
        self.registry.register(MANIFEST)
        self.runtime = AgentRuntime(self.registry)

    def tearDown(self):
        self.tmp.cleanup()

    def test_runtime_denies_disabled_capability(self):
        self.runtime.register_handler("internal.echo", lambda args: {"echo": args})
        with self.assertRaises(RuntimeErrorBase):
            self.runtime.execute("internal.echo", {"x": 1})

    def test_runtime_executes_only_enabled_registered_handler(self):
        self.registry.set_enabled("internal.echo", True, reviewed=True)
        self.runtime.register_handler("internal.echo", lambda args: {"echo": args})
        result = self.runtime.execute("internal.echo", {"x": 1})
        self.assertEqual(result["result"], {"echo": {"x": 1}})
        self.assertFalse(result["verified"])

    def test_runtime_requires_approval_for_high_risk(self):
        manifest = dict(MANIFEST, id="internal.publish", risk="high")
        self.registry.register(manifest)
        self.registry.set_enabled("internal.publish", True, reviewed=True)
        self.runtime.register_handler("internal.publish", lambda args: {"ok": True})
        with self.assertRaises(RuntimeErrorBase):
            self.runtime.execute("internal.publish", {})
        result = self.runtime.execute("internal.publish", {}, approval_status="approved")
        self.assertEqual(result["status"], "completed")


if __name__ == "__main__":
    unittest.main()
