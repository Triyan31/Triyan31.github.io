#!/usr/bin/env python3
"""Safe academic metadata sync.

Policy:
- Existing verified DOI records may be enriched from Crossref.
- Name-only search results are discovery candidates only.
- Discovery NEVER auto-publishes into publications.json.
- Unknown records are written to data/academic-review.json for manual review.
"""
from __future__ import annotations

import json
import pathlib
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBS = DATA / "publications.json"
IDENTITY = DATA / "academic-identity.json"
REVIEW = DATA / "academic-review.json"
USER_AGENT = "Triyan31-academic-sync/1.0 (GitHub Pages academic portfolio)"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def crossref_doi(doi):
    encoded = urllib.parse.quote(doi, safe="/")
    return get_json(f"https://api.crossref.org/v1/works/{encoded}")["message"]


def crossref_author(name, rows=20):
    q = urllib.parse.urlencode({"query.author": name, "rows": rows})
    return get_json(f"https://api.crossref.org/v1/works?{q}")["message"]["items"]


def author_names(item):
    out = []
    for a in item.get("author", []):
        out.append(" ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip())
    return out


def title(item):
    values = item.get("title") or []
    return values[0].strip() if values else None


def year(item):
    for field in ("published-print", "published-online", "published", "issued"):
        parts = item.get(field, {}).get("date-parts", [])
        if parts and parts[0]:
            return parts[0][0]
    return None


def normalized_doi(value):
    return (value or "").lower().strip().removeprefix("https://doi.org/")


def main():
    pubs = load(PUBS)
    identity = load(IDENTITY)
    person = identity["person"]["name"]
    existing = {normalized_doi(p.get("doi")) for p in pubs.get("publications", []) if p.get("doi")}

    # Validate/enrich only records already explicitly verified by the portfolio owner.
    validation = []
    for p in pubs.get("publications", []):
        doi = normalized_doi(p.get("doi"))
        if not doi or p.get("verification") != "verified":
            continue
        try:
            meta = crossref_doi(doi)
            validation.append({
                "doi": doi,
                "status": "resolved",
                "crossref_title": title(meta),
                "crossref_year": year(meta),
                "crossref_authors": author_names(meta),
                "publisher": meta.get("publisher"),
                "type": meta.get("type"),
            })
        except Exception as exc:
            validation.append({"doi": doi, "status": "lookup_failed", "error": str(exc)[:240]})

    # Discover by name, but never treat a name match as proof of authorship.
    candidates = []
    try:
        for item in crossref_author(person):
            doi = normalized_doi(item.get("DOI"))
            if not doi or doi in existing:
                continue
            candidates.append({
                "doi": doi,
                "title": title(item),
                "year": year(item),
                "venue": (item.get("container-title") or [None])[0],
                "authors": author_names(item),
                "publisher": item.get("publisher"),
                "source": "crossref-name-discovery",
                "verification": "needs_review",
                "reason": "Name search is not sufficient evidence of authorship; corroborate against verified academic identifiers, affiliation, publisher page, or manual review."
            })
    except Exception as exc:
        candidates.append({"source": "crossref-name-discovery", "verification": "lookup_failed", "error": str(exc)[:240]})

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "person": person,
        "policy": {
            "auto_publish": False,
            "name_match_is_proof": False,
            "verified_publications_mutated": False,
            "review_required": True
        },
        "verified_doi_validation": validation,
        "discovered_candidates": candidates
    }
    REVIEW.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Validated {len(validation)} verified DOI(s); discovered {len(candidates)} review candidate(s).")


if __name__ == "__main__":
    main()
