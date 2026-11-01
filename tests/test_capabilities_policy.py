import tempfile
import unittest
from pathlib import Path

from osihub.agent.capabilities import CapabilityError, CapabilityRegistry
from osihub.agent.policy import ApprovalError, ApprovalLedger, action_digest


MANIFEST = {
    "id": "research.scrapling",
    "name": "Scrapling research worker",
    "description": "Optional isolated web extraction worker",
    "source_url": "https://github.com/D4Vinci/Scrapling",
    "source_version": "un-pinned",
    "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}},
    "output_schema": {"type": "object"},
    "risk": "medium",
    "permissions": ["network"],
}


class CapabilityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "omnia.sqlite3")
        self.registry = CapabilityRegistry(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_registration_is_default_deny(self):
        item = self.registry.register(MANIFEST)
        self.assertFalse(item["enabled"])
        self.assertFalse(item["reviewed"])

    def test_enable_requires_explicit_review(self):
        self.registry.register(MANIFEST)
        with self.assertRaises(CapabilityError):
            self.registry.set_enabled(MANIFEST["id"], True)
        enabled = self.registry.set_enabled(MANIFEST["id"], True, reviewed=True)
        self.assertTrue(enabled["enabled"])
        self.assertTrue(enabled["reviewed"])

    def test_invalid_permission_is_rejected(self):
        invalid = dict(MANIFEST, permissions=["root_shell"])
        with self.assertRaises(CapabilityError):
            self.registry.register(invalid)

    def test_approval_binds_exact_action(self):
        ledger = ApprovalLedger(self.db)
        request = ledger.request("research.scrapling", "https://example.org",
                                 {"url": "https://example.org"}, ["network"],
                                 "v1", "medium")
        self.assertEqual(request["status"], "pending")
        with self.assertRaises(ApprovalError):
            ledger.decide(request["approval_id"], True, "wrong-digest")
        decided = ledger.decide(request["approval_id"], True, request["digest"])
        self.assertEqual(decided["status"], "approved")

    def test_digest_changes_when_arguments_change(self):
        first = action_digest("tool.x", "target", {"q": "one"}, ["network"], "v1")
        second = action_digest("tool.x", "target", {"q": "two"}, ["network"], "v1")
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
