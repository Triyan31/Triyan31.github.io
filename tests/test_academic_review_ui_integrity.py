import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AcademicReviewUIIntegrityTests(unittest.TestCase):
    def test_integrity_boundary_loads_before_review_application(self):
        html = (ROOT / "review.html").read_text(encoding="utf-8")
        boundary = html.index('src="./review-integrity.js"')
        application = html.index('src="./review.js"')
        self.assertLess(boundary, application)

    def test_decision_history_non_ok_response_is_fail_closed(self):
        source = (ROOT / "review-integrity.js").read_text(encoding="utf-8")
        self.assertIn("academic-decisions.json", source)
        self.assertIn("if (!response || !response.ok)", source)
        self.assertIn("throw new Error(`decision history unavailable", source)
        self.assertIn("global.fetch = async function failClosedAcademicFetch", source)

    def test_review_application_error_path_hides_decision_queue(self):
        source = (ROOT / "review.js").read_text(encoding="utf-8")
        self.assertIn("Unable to load review data", source)
        self.assertIn("Review queue unavailable.", source)


if __name__ == "__main__":
    unittest.main()
