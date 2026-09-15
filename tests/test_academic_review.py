import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_academic


class AcademicReviewSafetyTests(unittest.TestCase):
    def test_exact_registered_name_is_accepted(self):
        candidate = {"authors": ["Triyan Agung Laksono", "Widyastuti Andriyani"]}
        self.assertTrue(review_academic.candidate_has_registered_name("Triyan Agung Laksono", candidate))

    def test_short_similar_name_is_rejected(self):
        candidate = {"authors": ["Agung Laksono"]}
        self.assertFalse(review_academic.candidate_has_registered_name("Triyan Agung Laksono", candidate))

    def test_other_laksono_name_is_rejected(self):
        candidate = {"authors": ["Agung Dwi Laksono", "Ade Agung Laksono"]}
        self.assertFalse(review_academic.candidate_has_registered_name("Triyan Agung Laksono", candidate))

    def test_normalization_allows_case_and_diacritic_equivalence_only(self):
        candidate = {"authors": ["TRIYAN AGUNG LAKSONO"]}
        self.assertTrue(review_academic.candidate_has_registered_name("Triyan Agung Laksono", candidate))

    def test_missing_authors_fails_closed(self):
        self.assertFalse(review_academic.candidate_has_registered_name("Triyan Agung Laksono", {}))

    def test_doi_normalization(self):
        self.assertEqual(review_academic.doi_norm("https://doi.org/10.1234/ABC"), "10.1234/abc")

    def test_candidate_lookup_requires_exact_doi(self):
        report = {"discovered_candidates": [{"doi": "10.1234/abc", "title": "A"}]}
        self.assertEqual(review_academic.find_candidate(report, "https://doi.org/10.1234/ABC")["title"], "A")
        with self.assertRaises(SystemExit):
            review_academic.find_candidate(report, "10.1234/not-this")


if __name__ == "__main__":
    unittest.main()
