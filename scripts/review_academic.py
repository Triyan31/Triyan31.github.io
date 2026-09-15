#!/usr/bin/env python3
"""Safely approve or reject candidates from data/academic-review.json.

This helper never guesses authorship. Approval requires an explicit candidate DOI
and creates a public record marked `needs_review` unless the operator also supplies
publisher/manual evidence. Rejections are persisted so recurring discovery does not
keep presenting the same DOI.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REVIEW = DATA / "academic-review.json"
PUBS = DATA / "publications.json"
DECISIONS = DATA / "academic-decisions.json"


def load(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def doi_norm(value):
    value = (value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.strip()


def find_candidate(report, doi):
    target = doi_norm(doi)
    for candidate in report.get("discovered_candidates", []):
        if doi_norm(candidate.get("doi")) == target:
            return candidate
    raise SystemExit(f"Candidate DOI not found in current review queue: {target}")


def slug(text):
    import re
    value = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return value[:80] or "publication"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("approve", "reject"))
    parser.add_argument("--doi", required=True)
    parser.add_argument("--evidence-url")
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    report = load(REVIEW, {})
    pubs = load(PUBS, {"publications": []})
    decisions = load(DECISIONS, {"schema_version": 1, "decisions": []})
    candidate = find_candidate(report, args.doi)
    doi = doi_norm(candidate.get("doi"))
    now = datetime.now(timezone.utc).isoformat()

    # Replace the previous decision for the same DOI, preserving one canonical state.
    decisions["decisions"] = [d for d in decisions.get("decisions", []) if doi_norm(d.get("doi")) != doi]
    decision = {
        "doi": doi,
        "decision": args.action,
        "decided_at": now,
        "title": candidate.get("title"),
        "source": candidate.get("source"),
        "evidence_url": args.evidence_url,
        "note": args.note,
    }
    decisions["decisions"].append(decision)
    decisions["updated_at"] = now

    if args.action == "approve":
        if any(doi_norm(p.get("doi")) == doi for p in pubs.get("publications", [])):
            raise SystemExit(f"DOI already exists in publications.json: {doi}")
        # Approval from discovery is intentionally not equivalent to machine verification.
        # A direct evidence URL is required before adding the record to public data.
        if not args.evidence_url:
            raise SystemExit("Approval requires --evidence-url pointing to publisher/DOI/author-profile evidence.")
        publication = {
            "id": slug(candidate.get("title")),
            "year": candidate.get("year"),
            "title": candidate.get("title"),
            "venue": candidate.get("venue"),
            "authors": candidate.get("authors") or [],
            "keywords": [],
            "doi": doi,
            "url": args.evidence_url,
            "verification": "needs_review",
            "verification_sources": ["manual_review", candidate.get("source", "discovery")],
        }
        pubs.setdefault("publications", []).append(publication)
        pubs["updated_at"] = datetime.now(timezone.utc).date().isoformat()
        save(PUBS, pubs)

    save(DECISIONS, decisions)
    print(f"Recorded {args.action} decision for {doi}.")


if __name__ == "__main__":
    main()
