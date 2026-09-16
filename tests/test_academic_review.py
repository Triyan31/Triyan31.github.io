import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_academic
import sync_academic


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


class AcademicIdentityVerificationGateTests(unittest.TestCase):
    def test_exact_person_match_accepts_registered_name(self):
        ok, author, score = sync_academic.exact_person_match("Triyan Agung Laksono", ["Triyan Agung Laksono"])
        self.assertTrue(ok)
        self.assertEqual(author, "Triyan Agung Laksono")
        self.assertEqual(score, 1.0)

    def test_exact_person_match_rejects_similar_same_family_name(self):
        ok, author, score = sync_academic.exact_person_match("Triyan Agung Laksono", ["Agung Dwi Laksono"])
        self.assertFalse(ok)
        self.assertIsNone(author)
        self.assertEqual(score, 0.0)

    def test_fuzzy_signal_remains_available_for_discovery_only(self):
        discovery_ok, _, score = sync_academic.person_matches("Triyan Agung Laksono", ["Tri Agung Hari Laksono"])
        self.assertTrue(discovery_ok)
        self.assertGreaterEqual(score, 0.72)
        exact_ok, _, _ = sync_academic.exact_person_match("Triyan Agung Laksono", ["Tri Agung Hari Laksono"])
        self.assertFalse(exact_ok)

    def test_machine_source_gate_rejects_fuzzy_only_author(self):
        local = {"title": "Example Work", "year": 2024, "doi": "10.1234/example"}
        result = sync_academic.evaluate_source("Triyan Agung Laksono", local, "crossref", "Example Work", 2024, ["Tri Agung Hari Laksono"], "10.1234/example")
        self.assertFalse(result["author_match"])
        self.assertEqual(result["author_match_policy"], "exact_registered_name")

    def test_machine_source_gate_accepts_exact_normalized_author(self):
        local = {"title": "Example Work", "year": 2024, "doi": "10.1234/example"}
        result = sync_academic.evaluate_source("Triyan Agung Laksono", local, "crossref", "Example Work", 2024, ["TRIYAN AGUNG LAKSONO"], "10.1234/example")
        self.assertTrue(result["author_match"])
        self.assertEqual(result["author_similarity"], 1.0)

    def test_decision_fails_closed_when_only_author_identity_fails(self):
        evidence = [{"doi_match": True, "title_match": True, "author_match": False, "year_match": True}]
        status, reason = sync_academic.decision(evidence)
        self.assertEqual(status, "needs_review")
        self.assertIn("author identity", reason)


class AcademicEvidenceEnrichmentTests(unittest.TestCase):
    def test_crossref_exact_author_metadata_is_exposed_as_reported_evidence(self):
        item = {"author": [{"given": "Triyan Agung", "family": "Laksono", "ORCID": "https://orcid.org/0000-0002-1825-0097", "affiliation": [{"name": "Example University"}]}]}
        evidence = sync_academic.crossref_author_evidence(item, "Triyan Agung Laksono")
        self.assertTrue(evidence["exact_registered_name"])
        self.assertEqual(evidence["orcid"], "0000-0002-1825-0097")
        self.assertEqual(evidence["affiliations"], ["Example University"])
        self.assertEqual(evidence["evidence_status"], "reported_metadata")

    def test_similar_but_nonexact_author_does_not_inherit_identity_metadata(self):
        item = {"author": [{"given": "Agung Dwi", "family": "Laksono", "ORCID": "https://orcid.org/0000-0002-1825-0097", "affiliation": [{"name": "Other Institution"}]}]}
        evidence = sync_academic.crossref_author_evidence(item, "Triyan Agung Laksono")
        self.assertFalse(evidence["exact_registered_name"])
        self.assertIsNone(evidence["orcid"])
        self.assertEqual(evidence["affiliations"], [])
        self.assertEqual(evidence["evidence_status"], "not_established")

    def test_crossref_bibliographic_evidence_preserves_source_provenance(self):
        item = {"publisher": "Example Publisher", "container-title": ["Example Journal"], "type": "journal-article", "resource": {"primary": {"URL": "https://example.org/article"}}, "link": [{"URL": "https://example.org/pdf"}, {"URL": "https://example.org/pdf"}]}
        evidence = sync_academic.crossref_bibliographic_evidence(item)
        self.assertEqual(evidence["publisher"], "Example Publisher")
        self.assertEqual(evidence["venue"], "Example Journal")
        self.assertEqual(evidence["metadata_links"], ["https://example.org/pdf"])
        self.assertEqual(evidence["source"], "crossref")

    def test_orcid_normalization_does_not_invent_missing_identifier(self):
        self.assertEqual(sync_academic.normalized_orcid("https://orcid.org/0000-0002-1825-0097"), "0000-0002-1825-0097")
        self.assertIsNone(sync_academic.normalized_orcid(None))


class AcademicNormalizationEquivalenceTests(unittest.TestCase):
    def test_name_normalizers_are_behaviorally_equivalent_for_supported_inputs(self):
        cases = [
            None,
            "",
            "Triyan Agung Laksono",
            "  TRIYAN   AGUNG LAKSONO  ",
            "Tríyan Agung Laksono",
            "Triyan-Agung.Laksono",
            "A. B. Author",
            "Author 123",
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(review_academic.normalize_name(value), sync_academic.normalize(value))

    def test_doi_normalizers_are_behaviorally_equivalent_for_supported_inputs(self):
        cases = [
            None,
            "",
            "10.1234/ABC",
            " https://doi.org/10.1234/ABC ",
            "http://doi.org/10.1234/ABC",
            "doi:10.1234/ABC",
        ]
        for value in cases:
            with self.subTest(value=value):
                self.assertEqual(review_academic.doi_norm(value), sync_academic.normalized_doi(value))


if __name__ == "__main__":
    unittest.main()
