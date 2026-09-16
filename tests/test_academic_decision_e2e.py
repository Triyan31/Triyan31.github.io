import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SCRIPT = SCRIPTS / "review_academic.py"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("review_academic_e2e", SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class AcademicDecisionE2EIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        self.review_path = self.data / "academic-review.json"
        self.pubs_path = self.data / "publications.json"
        self.decisions_path = self.data / "academic-decisions.json"
        self.identity_path = self.data / "academic-identity.json"

        self.candidate = {
            "doi": "10.1234/example",
            "title": "Example Publication",
            "year": 2026,
            "venue": "Example Journal",
            "source": "test",
            "authors": ["Triyan A L"],
        }
        self._write(self.review_path, {"discovered_candidates": [self.candidate]})
        self._write(self.pubs_path, {"publications": []})
        self._write(self.decisions_path, {"schema_version": 1, "decisions": []})
        self._write(self.identity_path, {"person": {"name": "Triyan A L"}})

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _write(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def _run(self, action, actor="Triyan31", evidence_url=None):
        argv = ["review_academic.py", action, "--doi", "10.1234/example", "--actor", actor]
        if evidence_url:
            argv.extend(["--evidence-url", evidence_url])
        with patch.object(review, "REVIEW", self.review_path), \
             patch.object(review, "PUBS", self.pubs_path), \
             patch.object(review, "DECISIONS", self.decisions_path), \
             patch.object(review, "IDENTITY", self.identity_path), \
             patch.object(sys, "argv", argv):
            review.main()

    def test_reject_persists_authenticated_actor_and_keeps_queue_immutable(self):
        before = self.review_path.read_text(encoding="utf-8")
        self._run("reject")
        after = self.review_path.read_text(encoding="utf-8")
        history = json.loads(self.decisions_path.read_text(encoding="utf-8"))["decisions"]

        self.assertEqual(before, after)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["decision"], "reject")
        self.assertEqual(history[0]["decided_by"], "Triyan31")
        self.assertEqual(history[0]["doi"], "10.1234/example")

    def test_repeated_rejects_append_history_instead_of_overwriting(self):
        self._run("reject")
        first = json.loads(self.decisions_path.read_text(encoding="utf-8"))["decisions"][0]
        self._run("reject")
        history = json.loads(self.decisions_path.read_text(encoding="utf-8"))["decisions"]

        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], first)
        self.assertEqual([item["decision"] for item in history], ["reject", "reject"])
        self.assertTrue(all(item["decided_by"] == "Triyan31" for item in history))

    def test_invalid_actor_fails_closed_without_persisting_decision(self):
        before = self.decisions_path.read_text(encoding="utf-8")
        with self.assertRaises(SystemExit):
            self._run("reject", actor="bad actor!")
        self.assertEqual(self.decisions_path.read_text(encoding="utf-8"), before)

    def test_missing_candidate_fails_closed_without_mutation(self):
        self._write(self.review_path, {"discovered_candidates": []})
        before_decisions = self.decisions_path.read_text(encoding="utf-8")
        before_pubs = self.pubs_path.read_text(encoding="utf-8")
        with self.assertRaises(SystemExit):
            self._run("reject")
        self.assertEqual(self.decisions_path.read_text(encoding="utf-8"), before_decisions)
        self.assertEqual(self.pubs_path.read_text(encoding="utf-8"), before_pubs)

    def test_approval_without_evidence_fails_closed_without_mutation(self):
        before_decisions = self.decisions_path.read_text(encoding="utf-8")
        before_pubs = self.pubs_path.read_text(encoding="utf-8")
        with self.assertRaises(SystemExit):
            self._run("approve")
        self.assertEqual(self.decisions_path.read_text(encoding="utf-8"), before_decisions)
        self.assertEqual(self.pubs_path.read_text(encoding="utf-8"), before_pubs)

    def test_verified_approval_updates_registry_and_audit_history_together(self):
        verification = {
            "recommended_status": "verified",
            "reason": "Verified in isolated E2E fixture.",
            "evidence": [{"source": "fixture_registry"}],
        }
        with patch.object(review, "verify_publication", return_value=verification):
            self._run("approve", evidence_url="https://doi.org/10.1234/example")

        pubs = json.loads(self.pubs_path.read_text(encoding="utf-8"))["publications"]
        history = json.loads(self.decisions_path.read_text(encoding="utf-8"))["decisions"]
        self.assertEqual(len(pubs), 1)
        self.assertEqual(pubs[0]["verification"], "verified")
        self.assertEqual(pubs[0]["doi"], "10.1234/example")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["decision"], "approve")
        self.assertEqual(history[0]["decided_by"], "Triyan31")
        self.assertEqual(history[0]["machine_verification"]["status"], "verified")


if __name__ == "__main__":
    unittest.main()
