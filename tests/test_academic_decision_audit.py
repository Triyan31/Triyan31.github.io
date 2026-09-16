import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_academic


class AcademicDecisionActorAuditTests(unittest.TestCase):
    def test_decision_records_authenticated_actor(self):
        candidate = {"title": "Example Work", "source": "crossref-name-discovery"}
        decision = review_academic.build_decision(
            candidate,
            "10.1234/example",
            "reject",
            "Triyan31",
            "2026-09-16T00:00:00+00:00",
            note="Not mine",
        )
        self.assertEqual(decision["decided_by"], "Triyan31")
        self.assertEqual(decision["decision"], "reject")

    def test_missing_actor_fails_closed(self):
        with self.assertRaises(SystemExit):
            review_academic.normalize_actor("")

    def test_invalid_actor_fails_closed(self):
        for actor in ("bad actor", "actor/name", "@actor", "a" * 40):
            with self.subTest(actor=actor):
                with self.assertRaises(SystemExit):
                    review_academic.normalize_actor(actor)

    def test_valid_github_actor_shape_is_preserved(self):
        self.assertEqual(review_academic.normalize_actor("github-actions"), "github-actions")
        self.assertEqual(review_academic.normalize_actor("Triyan31"), "Triyan31")


if __name__ == "__main__":
    unittest.main()
