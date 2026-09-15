#!/usr/bin/env python3
"""Apply explicit academic review decisions safely.

Only explicit decisions in data/academic-decisions.json are actionable.
- reject: suppresses a discovered DOI from future discovery.
- approve: promotes a matching reviewed candidate only after live DOI metadata
  confirms DOI, title, author identity, and publication year.

Name similarity alone can never publish a record.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from difflib import SequenceMatcher

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBS = DATA / "publications.json"
REVIEW = DATA / "academic-review.json"
DECISIONS = DATA / "academic-decisions.json"
IDENTITY = DATA / "academic-identity.json"
USER_AGENT = "Triyan31-academic-decision-engine/1.0"
TITLE_THRESHOLD = 0.88


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, doc):
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).lower()
    return " ".join(re.findall(r"[a-z0-9]+", value))


def doi_norm(value):
    value = str(value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.strip()


def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def crossref(doi):
    encoded = urllib.parse.quote(doi, safe="/")
    req = urllib.request.Request(
        f"https://api.crossref.org/v1/works/{encoded}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)["message"]


def title(meta):
    values = meta.get("title") or []
    return values[0].strip() if values else ""


def year(meta):
    for field in ("published-print", "published-online", "published", "issued"):
        parts = meta.get(field, {}).get("date-parts", [])
        if parts and parts[0]:
            return parts[0][0]
    return None


def authors(meta):
    return [" ".join(x for x in (a.get("given", ""), a.get("family", "")) if x).strip() for a in meta.get("author", [])]


def author_match(person, names):
    target = normalize(person)
    target_family = target.split()[-1] if target else ""
    for name in names:
        candidate = normalize(name)
        if candidate == target:
            return True
        score = SequenceMatcher(None, target, candidate).ratio()
        if target_family and target_family in candidate.split() and score >= 0.72:
            return True
    return False


def slug(value):
    result = re.sub(r"[^a-z0-9]+", "-", normalize(value)).strip("-")
    return result[:80] or "publication"


def main():
    pubs = load(PUBS)
    review = load(REVIEW)
    decisions_doc = load(DECISIONS)
    identity = load(IDENTITY)
    person = identity["person"]["name"]

    candidates = {doi_norm(c.get("doi")): c for c in review.get("discovered_candidates", []) if c.get("doi")}
    existing = {doi_norm(p.get("doi")) for p in pubs.get("publications", []) if p.get("doi")}
    seen = set()
    promoted = 0
    rejected = 0
    changed_decisions = False

    for decision in decisions_doc.get("decisions", []):
        doi = doi_norm(decision.get("doi"))
        action = str(decision.get("decision") or "").strip().lower()
        if not doi or action not in {"approve", "reject"}:
            raise SystemExit(f"Invalid decision entry: DOI and decision=approve|reject required: {decision!r}")
        if doi in seen:
            raise SystemExit(f"Duplicate decision for DOI {doi}")
        seen.add(doi)

        if action == "reject":
            rejected += 1
            continue

        if doi in existing:
            decision["application_status"] = "already_public"
            continue

        candidate = candidates.get(doi)
        if not candidate:
            decision["application_status"] = "blocked"
            decision["application_reason"] = "Approved DOI is not present in the current reviewed-candidate set."
            changed_decisions = True
            continue

        try:
            meta = crossref(doi)
        except Exception as exc:
            decision["application_status"] = "blocked"
            decision["application_reason"] = f"Crossref lookup failed: {str(exc)[:180]}"
            changed_decisions = True
            continue

        source_title = title(meta)
        source_year = year(meta)
        source_authors = authors(meta)
        checks = {
            "doi": doi_norm(meta.get("DOI")) == doi,
            "title": similarity(candidate.get("title"), source_title) >= TITLE_THRESHOLD,
            "author": author_match(person, source_authors),
            "year": bool(candidate.get("year") and source_year and int(candidate["year"]) == int(source_year)),
        }
        if not all(checks.values()):
            failed = ", ".join(k for k, ok in checks.items() if not ok)
            decision["application_status"] = "blocked"
            decision["application_reason"] = f"Live bibliographic verification failed: {failed}."
            decision["verification_checks"] = checks
            changed_decisions = True
            continue

        record = {
            "id": slug(source_title),
            "year": source_year,
            "title": source_title,
            "venue": (meta.get("container-title") or [candidate.get("venue")])[0],
            "authors": source_authors,
            "keywords": [],
            "doi": meta.get("DOI", doi),
            "url": f"https://doi.org/{doi}",
            "verification": "verified",
            "verification_sources": ["manual_review", "crossref", "doi"],
        }
        pubs.setdefault("publications", []).append(record)
        existing.add(doi)
        promoted += 1
        decision["application_status"] = "applied"
        decision["applied_at"] = datetime.now(timezone.utc).isoformat()
        decision["verification_checks"] = checks
        changed_decisions = True

    if promoted:
        pubs["updated_at"] = datetime.now(timezone.utc).date().isoformat()
        save(PUBS, pubs)
    if changed_decisions:
        decisions_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
        save(DECISIONS, decisions_doc)

    print(f"Decision engine complete: {promoted} promoted, {rejected} rejected/suppressed, {len(decisions_doc.get('decisions', []))} explicit decision(s) processed.")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, TypeError) as exc:
        print(f"Decision engine failed closed: {exc}", file=sys.stderr)
        raise SystemExit(1)
