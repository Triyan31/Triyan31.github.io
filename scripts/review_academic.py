#!/usr/bin/env python3
"""Authenticated approve/reject decision engine for academic discovery candidates.

Reject decisions suppress recurring false positives. Approvals require explicit
source evidence, an exact registered author-name match in the candidate metadata,
and the DOI/title/author/year machine gate before a record can enter the public
verified registry. Every persisted decision records the authenticated actor supplied
by the trusted workflow boundary.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import datetime, timezone

from sync_academic import normalize, normalized_doi, verify_publication

# Compatibility aliases keep the review module's existing public helper names while
# making sync_academic the single canonical implementation of normalization rules.
normalize_name = normalize
doi_norm = normalized_doi

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REVIEW = DATA / "academic-review.json"
PUBS = DATA / "publications.json"
DECISIONS = DATA / "academic-decisions.json"
IDENTITY = DATA / "academic-identity.json"


def load(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def candidate_has_registered_name(person, candidate):
    target = normalize_name(person)
    return bool(target) and any(normalize_name(author) == target for author in candidate.get("authors") or [])


def find_candidate(report, doi):
    target = doi_norm(doi)
    for candidate in report.get("discovered_candidates", []):
        if doi_norm(candidate.get("doi")) == target:
            return candidate
    raise SystemExit(f"Candidate DOI not found in current review queue: {target}")


def normalize_actor(value):
    actor = (value or "").strip()
    if not actor or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", actor):
        raise SystemExit("Decision actor is missing or invalid; authenticated decisions are fail-closed.")
    return actor


def build_decision(candidate, doi, action, actor, now, evidence_url=None, note=""):
    return {
        "doi": doi,
        "decision": action,
        "decided_at": now,
        "decided_by": normalize_actor(actor),
        "title": candidate.get("title"),
        "source": candidate.get("source"),
        "evidence_url": evidence_url,
        "note": note,
    }


def slug(text):
    value = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return value[:80] or "publication"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("approve", "reject"))
    parser.add_argument("--doi", required=True)
    parser.add_argument("--actor", required=True, help="Authenticated GitHub actor performing the decision")
    parser.add_argument("--evidence-url")
    parser.add_argument("--note", default="")
    args = parser.parse_args()
    actor = normalize_actor(args.actor)

    report = load(REVIEW, {})
    pubs = load(PUBS, {"publications": []})
    identity = load(IDENTITY, {})
    decisions = load(DECISIONS, {"schema_version": 1, "decisions": []})
    candidate = find_candidate(report, args.doi)
    doi = doi_norm(candidate.get("doi"))
    now = datetime.now(timezone.utc).isoformat()

    if any(doi_norm(p.get("doi")) == doi for p in pubs.get("publications", [])):
        raise SystemExit(f"DOI already exists in publications.json: {doi}")

    verification_result = None
    publication = None
    if args.action == "approve":
        if not args.evidence_url:
            raise SystemExit("Approval requires --evidence-url pointing to publisher/DOI/author-profile evidence.")
        person = identity.get("person", {}).get("name")
        if not person:
            raise SystemExit("Academic identity name is unavailable; approval is fail-closed.")
        if not candidate_has_registered_name(person, candidate):
            raise SystemExit("Approval blocked: candidate metadata does not contain the exact registered academic identity name. Add a verified alias to the identity policy before allowing a name variant.")
        publication = {
            "id": slug(candidate.get("title")),
            "year": candidate.get("year"),
            "title": candidate.get("title"),
            "venue": candidate.get("venue"),
            "authors": candidate.get("authors") or [],
            "keywords": [],
            "doi": doi,
            "url": args.evidence_url,
            "verification": "unverified",
            "verification_sources": ["manual_review", candidate.get("source", "discovery")],
        }
        verification_result = verify_publication(person, publication)
        if verification_result.get("recommended_status") != "verified":
            reason = verification_result.get("reason", "Machine verification did not pass.")
            raise SystemExit(f"Approval blocked: {reason}")
        publication["verification"] = "verified"
        machine_sources = [e.get("source") for e in verification_result.get("evidence", []) if e.get("source")]
        publication["verification_sources"] = list(dict.fromkeys(publication["verification_sources"] + machine_sources))

    decisions["decisions"] = [d for d in decisions.get("decisions", []) if doi_norm(d.get("doi")) != doi]
    decision = build_decision(candidate, doi, args.action, actor, now, args.evidence_url, args.note)
    if verification_result:
        decision["machine_verification"] = {
            "status": verification_result.get("recommended_status"),
            "reason": verification_result.get("reason"),
            "sources": [e.get("source") for e in verification_result.get("evidence", []) if e.get("source")],
        }
    decisions["decisions"].append(decision)
    decisions["updated_at"] = now

    if publication:
        pubs.setdefault("publications", []).append(publication)
        pubs["updated_at"] = datetime.now(timezone.utc).date().isoformat()
        save(PUBS, pubs)

    save(DECISIONS, decisions)
    print(f"Recorded {args.action} decision for {doi} by {actor}.")
    if publication:
        print("Candidate passed the verification gate and was added as verified.")


if __name__ == "__main__":
    main()
