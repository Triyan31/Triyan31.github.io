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


class AcademicEvidenceEnrichmentTests(unittest.TestCase):
    def test_crossref_exact_author_metadata_is_exposed_as_reported_evidence(self):
        item = {
            "author": [
                {
                    "given": "Triyan Agung",
                    "family": "Laksono",
                    "ORCID": "https://orcid.org/0000-0002-1825-0097",
                    "affiliation": [{"name": "Example University"}],
                }
            ]
        }
        evidence = sync_academic.crossref_author_evidence(item, "Triyan Agung Laksono")
        self.assertTrue(evidence["exact_registered_name"])
        self.assertEqual(evidence["orcid"], "0000-0002-1825-0097")
        self.assertEqual(evidence["affiliations"], ["Example University"])
        self.assertEqual(evidence["evidence_status"], "reported_metadata")

    def test_similar_but_nonexact_author_does_not_inherit_identity_metadata(self):
        item = {
            "author": [
                {
                    "given": "Agung Dwi",
                    "family": "Laksono",
                    "ORCID": "https://orcid.org/0000-0002-1825-0097",
                    "affiliation": [{"name": "Other Institution"}],
                }
            ]
        }
        evidence = sync_academic.crossref_author_evidence(item, "Triyan Agung Laksono")
        self.assertFalse(evidence["exact_registered_name"])
        self.assertIsNone(evidence["orcid"])
        self.assertEqual(evidence["affiliations"], [])
        self.assertEqual(evidence["evidence_status"], "not_established")

    def test_crossref_bibliographic_evidence_preserves_source_provenance(self):
        item = {
            "publisher": "Example Publisher",
            "container-title": ["Example Journal"],
            "type": "journal-article",
            "resource": {"primary": {"URL": "https://example.org/article"}},
            "link": [{"URL": "https://example.org/pdf"}, {"URL": "https://example.org/pdf"}],
        }
        evidence = sync_academic.crossref_bibliographic_evidence(item)
        self.assertEqual(evidence["publisher"], "Example Publisher")
        self.assertEqual(evidence["venue"], "Example Journal")
        self.assertEqual(evidence["metadata_links"], ["https://example.org/pdf"])
        self.assertEqual(evidence["source"], "crossref")

    def test_orcid_normalization_does_not_invent_missing_identifier(self):
        self.assertEqual(sync_academic.normalized_orcid("https://orcid.org/0000-0002-1825-0097"), "0000-0002-1825-0097")
        self.assertIsNone(sync_academic.normalized_orcid(None))


if __name__ == "__main__":
    unittest.main()
