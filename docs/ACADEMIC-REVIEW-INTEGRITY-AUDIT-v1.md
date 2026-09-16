# Academic Review Integrity Audit v1

**Baseline:** `main` at merge commit `1980b367c0baa1f9a7af68d7c48746f57f9e06ba` (PR #18)

**Scope:** discovery → evidence → review UI → authenticated decision → append-only history → publication state.

## Executive result

The subsystem has a strong fail-closed baseline, but it is **not ready to freeze as v1 yet**. The audit found two integrity gaps that should be fixed before freeze. No production code is changed by this audit branch.

## Controls confirmed

- Discovery/name similarity is not treated as proof of authorship.
- Machine verification requires DOI, title, exact registered author identity, and year to match the primary bibliographic source.
- Approval requires explicit evidence and fails closed when identity/evidence verification is unavailable or mismatched.
- Decision actor is supplied by the authenticated GitHub Actions boundary and validated before persistence.
- Decision history is append-only; current state is derived from the latest decision per DOI.
- Reject decisions suppress rediscovery while preserving earlier history.
- Review queue data is not mutated by the decision engine.
- Existing public DOI records cannot be approved again through the review decision path.
- PR safety tests cover actor integrity, append-only semantics, latest-decision semantics, and end-to-end approve/reject behavior.

## Findings

### ARI-01 — HIGH — publication and decision persistence are not atomic

On a successful approval, `review_academic.py` writes `publications.json` first and `academic-decisions.json` second. If the second write fails after the publication write succeeds, a verified publication can exist without its corresponding audit decision. The current E2E test proves the normal success path but does not inject a failure between these two writes.

**Required remediation:** make the approval persistence transaction-like for repository files (for example, prepare both complete documents first and use rollback-safe replacement), or otherwise guarantee that a partial write cannot leave publication state ahead of audit history. Add a regression test that injects failure during the second persistence operation and proves no partial approved state survives.

### ARI-02 — MEDIUM — review UI does not fail closed when decision history cannot be loaded

`review.js` fetches `academic-review.json` and `academic-decisions.json` together, but only treats failure of the review report as fatal. If the decisions request returns a non-OK response, the UI continues with an empty decision map. Previously approved/rejected candidates can therefore be rendered as `needs_review` and decision controls can be shown again. The trusted workflow/backend still prevents some unsafe outcomes, so this is not equivalent to an authorization bypass, but the UI state is not integrity-safe.

**Required remediation:** if `academic-decisions.json` cannot be loaded or parsed, render the review console read-only/unavailable and do not expose approve/reject controls. Add a UI regression test or deterministic testable helper covering this failure state.

## Residual observations

- `academic-safety-tests.yml` validates JSON syntax for identity, publications, and decisions, but not `academic-review.json` or `data/academic.json`. This is lower priority because the review report is generated, but adding validation would improve CI completeness.
- The decision workflow runs tests before committing reviewed data, which is a useful safety gate. Concurrency serialization also reduces simultaneous decision races.
- The workflow pushes directly to `main`; repository branch/ruleset enforcement was not established by this code audit and should not be assumed from application code alone.

## Freeze gate

Do **not** declare Academic Review baseline v1 frozen yet.

Freeze criteria:

1. ARI-01 fixed with failure-injection regression coverage.
2. ARI-02 fixed with fail-closed UI coverage.
3. Academic safety tests pass on the remediation PR(s).
4. Final audit confirms no new integrity regression.

## Change policy for this audit

This branch is intentionally audit-only. Remediation must be isolated in separate branch/PR(s), preserving the existing PR safety workflow.