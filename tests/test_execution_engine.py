import tempfile
import unittest
from pathlib import Path

from osihub.agent.capabilities import CapabilityRegistry
from osihub.agent.policy import ApprovalLedger
from osihub.agent.runtime import AgentRuntime
from osihub.agent.engine import ExecutionEngine, ExecutionError, validate_schema


MANIFEST = {
    "id": "local.echo", "name": "Echo", "description": "Test-only trusted handler",
    "source_url": "https://example.invalid/echo", "source_version": "1.0",
    "input_schema": {"type": "object", "required": ["text"],
                     "properties": {"text": {"type": "string", "maxLength": 50}},
                     "additionalProperties": False},
    "output_schema": {"type": "object", "required": ["echo"],
                      "properties": {"echo": {"type": "string"}}},
    "risk": "low", "permissions": []
}


class ExecutionEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "omnia.sqlite3")
        self.registry = CapabilityRegistry(self.db)
        self.registry.register(MANIFEST)
        self.registry.set_enabled("local.echo", True, reviewed=True)
        self.ledger = ApprovalLedger(self.db)
        self.runtime = AgentRuntime(self.registry)
        self.runtime.register_handler("local.echo", lambda args: {"echo": args["text"]})
        self.engine = ExecutionEngine(self.registry, self.ledger, self.runtime, self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_executes_only_registered_handler_and_records_result(self):
        result = self.engine.execute("local.echo", {"text": "hello"})
        self.assertEqual(result["result"], {"echo": "hello"})
        self.assertFalse(result["verified"])
        record = self.engine.get_execution(result["execution_id"])
        self.assertEqual(record["status"], "completed")

    def test_input_schema_rejects_extra_or_invalid_fields(self):
        with self.assertRaises(ExecutionError):
            self.engine.execute("local.echo", {"text": "ok", "shell": "id"})
        with self.assertRaises(ExecutionError):
            self.engine.execute("local.echo", {"text": 123})

    def test_medium_risk_requires_exact_approval(self):
        medium = dict(MANIFEST, id="local.medium", risk="medium")
        self.registry.register(medium)
        self.registry.set_enabled("local.medium", True, reviewed=True)
        self.runtime.register_handler("local.medium", lambda args: {"echo": args["text"]})
        with self.assertRaises(ExecutionError):
            self.engine.execute("local.medium", {"text": "approved?"})
        request = self.ledger.request("local.medium", "local", {"text": "approved?"},
                                     [], "1.0", "medium")
        self.ledger.decide(request["approval_id"], True, request["digest"])
        result = self.engine.execute("local.medium", {"text": "approved?"},
                                     approval_id=request["approval_id"])
        self.assertEqual(result["status"], "completed")
        with self.assertRaises(ExecutionError):
            self.engine.execute("local.medium", {"text": "approved?"},
                                approval_id=request["approval_id"])
        with self.assertRaises(ExecutionError):
            self.engine.execute("local.medium", {"text": "different"},
                                approval_id=request["approval_id"])

    def test_disabled_capability_is_denied(self):
        self.registry.set_enabled("local.echo", False)
        with self.assertRaises(ExecutionError):
            self.engine.execute("local.echo", {"text": "no"})


if __name__ == "__main__":
    unittest.main()
