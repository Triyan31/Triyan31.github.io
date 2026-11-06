# Research & Publications V1 Audit

**Audit date:** 2026-09-21

**Audited baseline:** main commit 896f1d20efd9735d08c162581b8f37f158bc0517

**Scope:** public research presentation, publication registry, academic discovery/verification pipeline, decision persistence, and synchronization behavior.

## Audit objective

Verify that the public Research/Publication surface remains a controlled academic registry rather than an uncontrolled name-search feed, and identify the next bounded improvement without weakening the Academic Review v1 integrity guarantees.

## Current architecture

The repository currently separates four concerns:

1. Public publication registry — data/publications.json
2. Verification/discovery report — data/academic-review.json
3. Append-only review decisions — data/academic-decisions.json
4. Academic identity registry — data/academic-identity.json

The public homepage reads only verified records from data/publications.json. Discovery candidates are not rendered as publications.

## Verified public registry

At the audited baseline:

- Public records: **5**
- Machine-verified: **3**
- Manual/publisher-verified: **2**
- Needs review among current public records: **0**
- Discovery candidates awaiting review: **2**
- Explicitly rejected/suppressed candidates: **15**

The five public records are explicitly marked verification: verified and contain publisher/DOI provenance appropriate to their record type.

## Integrity findings

### RP-01 — Public auto-publication boundary: PASS

data/publications.json is not populated directly from name discovery.

scripts/sync_academic.py verifies existing public records and writes the review report; it does not automatically add discovered candidates to publications.json.

**Assessment:** no change required.

### RP-02 — Rejected discovery suppression: PASS

The academic sync derives the latest decision for each DOI from the append-only decision history. A candidate whose latest decision is reject is placed in suppressed_candidates rather than being returned as an active review candidate.

**Assessment:** the previously discussed rejected-article reappearance problem is addressed at the current sync layer.

### RP-03 — Public record deletion safety: PASS

The sync script does not auto-delete public publication records. This means removing a record from data/publications.json is not undone by the scheduled academic discovery process.

**Assessment:** safe by design. A public record can only return if it is intentionally reintroduced by a later repository change/workflow path.

### RP-04 — Approval safety boundary: PASS

The authenticated review workflow records the decision actor, refreshes academic verification, runs Academic Safety Tests, and commits reviewed academic data only after the safety step.

**Assessment:** preserve the existing workflow. Do not bypass it with client-side publication mutation.

### RP-05 — Homepage publication rendering: MINOR CONSISTENCY GAP

index.html contains three hard-coded publication entries as initial/fallback markup, while script.js subsequently replaces the publication list with the verified records from data/publications.json.

This creates two representations of the same public content:

- static fallback: 3 records;
- data-driven registry: currently 5 records.

This does not currently create an authorship-integrity failure because the runtime registry is the authoritative rendered source, but it creates stale-content risk if JavaScript or the publication JSON fails to load.

**Assessment:** bounded follow-up recommended.

### RP-06 — Manual verification records: PASS WITH DOCUMENTATION CAVEAT

Two DOI-less publications remain manually verified based on publisher evidence. The code correctly does not pretend that DOI-less records are machine-verified.

**Assessment:** retain. Future manual verification should preserve publisher evidence in the registry/review documentation.

### RP-07 — Identity registry: PASS

The registered person name is Triyan Agung Laksono. The verification policy explicitly rejects name similarity as sufficient proof and keeps fuzzy matching as discovery context only.

**Assessment:** no change required.

## Important boundary

The Research page should remain a public publication registry, not a mirror of Google Scholar, Crossref, OpenAlex, SINTA, or another external profile.

External sources may discover candidates and provide evidence. They should not silently become public portfolio records.

Likewise, the public site should not expose:

- review decisions as an administrative control surface;
- private review notes;
- student or institutional data;
- unpublished manuscripts;
- records whose authorship has not been verified.

## Recommended next implementation

The next bounded change should address RP-05 only:

### Research/Publications rendering consistency

Move the initial publication markup fully behind the data-driven rendering contract so there is one authoritative publication representation.

Requirements:

- keep data/publications.json as the public registry;
- render only records with verification === verified;
- retain fail-safe behavior when the registry cannot be loaded;
- avoid inventing fallback publication records in HTML;
- preserve the existing visual language;
- do not change Academic Review v1 decision semantics;
- add regression coverage for the publication rendering contract.

This should be a dedicated PR and should not modify the certified Academic Review workflow or decision model.

## Non-goals

This audit does not recommend:

- adding automatic publication ingestion;
- auto-publishing discovered records;
- auto-deleting public records;
- replacing manual verification with fuzzy matching;
- adding a full research-management system;
- importing Google Scholar/SINTA/ORCID data directly into the public registry;
- exposing the review console through the public Research page.

## Audit conclusion

The current Research/Publication data boundary is structurally sound. The principal remaining issue is a small presentation-layer duplication between static homepage markup and the authoritative publication registry.

The next change should therefore be a narrow Research Publication Rendering Consistency PR rather than another broad academic-integrity redesign.
