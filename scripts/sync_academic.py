#!/usr/bin/env python3
"""Evidence-based academic metadata verification.

Safety policy:
- Public publications are never auto-deleted or silently rewritten.
- DOI records are checked against Crossref and, when available, OpenAlex.
- Verification compares DOI, normalized title, author identity, and year.
- Ambiguous/mismatched records go to data/academic-review.json.
- Name-only discoveries are always needs_review and never auto-published.
- DOI-less publisher records remain manual-review records.
- Explicit review decisions are persisted so rejected candidates do not reappear.
"""
from __future__ import annotations

import difflib
import json
import pathlib
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBS = DATA / "publications.json"
IDENTITY = DATA / "academic-identity.json"
REVIEW = DATA / "academic-review.json"
DECISIONS = DATA / "academic-decisions.json"
USER_AGENT = "Triyan31-academic-sync/2.1 (GitHub Pages academic portfolio)"
TITLE_THRESHOLD = 0.88


def load(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def crossref_doi(doi):
    encoded = urllib.parse.quote(doi, safe="/")
    return get_json(f"https://api.crossref.org/v1/works/{encoded}")["message"]


def crossref_author(name, rows=20):
    query = urllib.parse.urlencode({"query.author": name, "rows": rows})
    return get_json(f"https://api.crossref.org/v1/works?{query}")["message"]["items"]


def openalex_doi(doi):
    encoded = urllib.parse.quote(f"https://doi.org/{doi}", safe="")
    return get_json(f"https://api.openalex.org/works/{encoded}")


def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).lower()
    return " ".join(re.findall(r"[a-z0-9]+", value))


def normalized_doi(value):
    value = (value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.strip()


def similarity(a, b):
    return round(difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio(), 4)


def crossref_author_names(item):
    return [" ".join(x for x in (a.get("given", ""), a.get("family", "")) if x).strip() for a in item.get("author", [])]


def openalex_author_names(item):
    return [a.get("author", {}).get("display_name", "").strip() for a in item.get("authorships", []) if a.get("author")]


def crossref_title(item):
    values = item.get("title") or []
    return values[0].strip() if values else None


def crossref_year(item):
    for field in ("published-print", "published-online", "published", "issued"):
        parts = item.get(field, {}).get("date-parts", [])
        if parts and parts[0]:
            return parts[0][0]
    return None


def person_matches(person, authors):
    target = normalize(person)
    target_parts = target.split()
    family = target_parts[-1] if target_parts else ""
    for author in authors:
        candidate = normalize(author)
        if candidate == target:
            return True, author, 1.0
        score = difflib.SequenceMatcher(None, target, candidate).ratio()
        if family and family in candidate.split() and score >= 0.72:
            return True, author, round(score, 4)
    return False, None, 0.0


def evaluate_source(person, local, source_name, source_title, source_year, source_authors, source_doi=None):
    title_score = similarity(local.get("title"), source_title)
    author_ok, matched_author, author_score = person_matches(person, source_authors)
    local_year = local.get("year")
    year_ok = bool(local_year and source_year and int(local_year) == int(source_year))
    doi_ok = True if not local.get("doi") else normalized_doi(local.get("doi")) == normalized_doi(source_doi or local.get("doi"))
    return {
        "source": source_name,
        "doi_match": doi_ok,
        "title_match": title_score >= TITLE_THRESHOLD,
        "title_similarity": title_score,
        "author_match": author_ok,
        "matched_author": matched_author,
        "author_similarity": author_score,
        "year_match": year_ok,
        "source_title": source_title,
        "source_year": source_year,
        "source_authors": source_authors,
    }


def decision(evidence):
    if not evidence:
        return "needs_review", "No machine-verifiable bibliographic source resolved."
    primary = evidence[0]
    core = primary["doi_match"] and primary["title_match"] and primary["author_match"] and primary["year_match"]
    if core:
        return "verified", "DOI, title, author identity, and year match the primary bibliographic source."
    failed = [label for key, label in (("doi_match", "DOI"), ("title_match", "title"), ("author_match", "author"), ("year_match", "year")) if not primary[key]]
    return "needs_review", f"Primary-source comparison requires review: {', '.join(failed)} did not match confidently."


def verify_publication(person, publication):
    doi = normalized_doi(publication.get("doi"))
    result = {"id": publication.get("id"), "title": publication.get("title"), "doi": doi or None, "current_status": publication.get("verification", "unverified"), "evidence": []}
    if not doi:
        result["recommended_status"] = "manual_verified" if "publisher" in publication.get("verification_sources", []) else "needs_review"
        result["reason"] = "No DOI is recorded; retain only with direct publisher/manual evidence."
        return result
    try:
        meta = crossref_doi(doi)
        result["evidence"].append(evaluate_source(person, publication, "crossref", crossref_title(meta), crossref_year(meta), crossref_author_names(meta), meta.get("DOI")))
    except Exception as exc:
        result["crossref_error"] = str(exc)[:240]
    try:
        meta = openalex_doi(doi)
        result["evidence"].append(evaluate_source(person, publication, "openalex", meta.get("title"), meta.get("publication_year"), openalex_author_names(meta), (meta.get("ids") or {}).get("doi")))
    except Exception as exc:
        result["openalex_error"] = str(exc)[:240]
    status, reason = decision(result["evidence"])
    result["recommended_status"] = status
    result["reason"] = reason
    result["status_changed"] = result["current_status"] != status
    return result


def main():
    pubs = load(PUBS)
    identity = load(IDENTITY)
    decisions_doc = load(DECISIONS, {"decisions": []})
    decisions = {normalized_doi(d.get("doi")): d for d in decisions_doc.get("decisions", []) if d.get("doi")}
    person = identity["person"]["name"]
    records = pubs.get("publications", [])
    existing = {normalized_doi(p.get("doi")) for p in records if p.get("doi")}
    verification = [verify_publication(person, publication) for publication in records]

    candidates = []
    suppressed = []
    try:
        for item in crossref_author(person):
            doi = normalized_doi(item.get("DOI"))
            if not doi or doi in existing:
                continue
            prior = decisions.get(doi)
            if prior and prior.get("decision") == "reject":
                suppressed.append({"doi": doi, "title": crossref_title(item), "decision": "reject", "decided_at": prior.get("decided_at")})
                continue
            authors = crossref_author_names(item)
            author_ok, matched_author, author_score = person_matches(person, authors)
            candidate = {
                "doi": doi,
                "title": crossref_title(item),
                "year": crossref_year(item),
                "venue": (item.get("container-title") or [None])[0],
                "authors": authors,
                "publisher": item.get("publisher"),
                "source": "crossref-name-discovery",
                "verification": "needs_review",
                "identity_name_match": author_ok,
                "matched_author": matched_author,
                "author_similarity": author_score,
                "reason": "Discovery is not proof of authorship. Confirm against publisher, DOI metadata, affiliation, ORCID/author profile, or manual evidence before publishing."
            }
            if prior:
                candidate["prior_decision"] = prior
            candidates.append(candidate)
    except Exception as exc:
        candidates.append({"source": "crossref-name-discovery", "verification": "lookup_failed", "error": str(exc)[:240]})

    report = {
        "schema_version": 3,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "person": person,
        "policy": {
            "auto_publish": False,
            "auto_delete": False,
            "auto_mutate_public_records": False,
            "name_match_is_proof": False,
            "machine_verified_rule": "DOI + normalized title + author identity + publication year must match primary bibliographic metadata.",
            "manual_verified_rule": "DOI-less or incomplete-metadata works require direct publisher/manual evidence.",
            "title_similarity_threshold": TITLE_THRESHOLD,
            "review_required_for_mismatch": True,
            "rejected_candidates_suppressed": True
        },
        "verification_summary": {
            "total_public_records": len(records),
            "machine_verified": sum(v.get("recommended_status") == "verified" for v in verification),
            "manual_verified": sum(v.get("recommended_status") == "manual_verified" for v in verification),
            "needs_review": sum(v.get("recommended_status") == "needs_review" for v in verification),
            "discovered_needs_review": len(candidates),
            "suppressed_rejections": len(suppressed)
        },
        "publication_verification": verification,
        "discovered_candidates": candidates,
        "suppressed_candidates": suppressed
    }
    REVIEW.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["verification_summary"]
    print(f"Checked {summary['total_public_records']} public record(s): {summary['machine_verified']} machine verified, {summary['manual_verified']} manual-source verified, {summary['needs_review']} need review; discovered {len(candidates)} candidate(s), suppressed {len(suppressed)} rejected candidate(s).")


if __name__ == "__main__":
    main()
