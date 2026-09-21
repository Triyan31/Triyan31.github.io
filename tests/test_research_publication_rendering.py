import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "index.html"
SCRIPT_JS = ROOT / "script.js"
PUBLICATIONS = ROOT / "data" / "publications.json"


class ResearchPublicationRenderingContractTests(unittest.TestCase):
    def test_homepage_does_not_contain_hard_coded_publication_records(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('class="publication-list reveal"', html)
        self.assertIn("Loading verified research registry", html)
        self.assertNotIn("Digital Activity Location Clustering Based on Twitter Geospatial Data", html)
        self.assertNotIn("Imbalanced Data Handling for Stroke Prediction", html)
        self.assertNotIn("Multi-class Imbalanced Data Classification on Statlog (Shuttle)", html)

    def test_publication_renderer_uses_verified_registry(self):
        source = SCRIPT_JS.read_text(encoding="utf-8")
        self.assertIn("loadJson('./data/publications.json')", source)
        self.assertIn("p.verification === 'verified'", source)
        self.assertIn("renderPublications(results[1].value)", source)

    def test_publication_failure_is_fail_closed(self):
        source = SCRIPT_JS.read_text(encoding="utf-8")
        self.assertIn("Research registry unavailable.", source)
        self.assertIn("No publication records are shown until the registry is available.", source)

    def test_registry_contains_only_verified_public_records_for_rendering_contract(self):
        data = json.loads(PUBLICATIONS.read_text(encoding="utf-8"))
        records = data.get("publications")
        self.assertIsInstance(records, list)
        self.assertTrue(records)
        for record in records:
            self.assertEqual(record.get("verification"), "verified")
            self.assertTrue(record.get("title", "").strip())
            self.assertTrue(record.get("venue", "").strip())

    def test_renderer_does_not_use_hard_coded_publication_title_literals(self):
        source = SCRIPT_JS.read_text(encoding="utf-8")
        for title in (
            "Digital Activity Location Clustering Based on Twitter Geospatial Data",
            "Imbalanced Data Handling for Stroke Prediction",
            "Multi-class Imbalanced Data Classification on Statlog (Shuttle)",
        ):
            self.assertNotIn(title, source)


if __name__ == "__main__":
    unittest.main()
