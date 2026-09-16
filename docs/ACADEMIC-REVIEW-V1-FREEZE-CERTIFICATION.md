# Academic Review v1 Freeze Certification

**Certification date:** 2026-09-16

**Certified baseline:** `main` commit `25587bd919e6656ba0058a2ae28ae101b52aad0f` (merge of PR #22)

**Scope:** discovery → evidence → review UI → authenticated decision → append-only decision history → publication persistence → CI integrity gates.

## Certification result

**PASS — Academic Review v1 is eligible to be frozen at the certified baseline.**

This certification supersedes the freeze-blocking conclusion in `ACADEMIC-REVIEW-INTEGRITY-AUDIT-v1.md`. The two blockers identified by that audit (ARI-01 and ARI-02) were remediated before this baseline, followed by additional history-integrity, end-to-end, fail-closed, and JSON-validation hardening.

## Baseline verification

The certified `main` HEAD is `25587bd919e6656ba0058a2ae28ae101b52aad0f`.

GitHub Actions `Academic safety tests` run #42 executed against that exact `main` commit and completed successfully. The successful job includes:

- Python compilation;
- Academic regression/safety tests;
- Academic JSON syntax validation, including `data/academic-review.json`.

GitHub Pages build/deployment for the same baseline also completed successfully.

## Integrity controls certified

The v1 baseline now includes the following controls established during the hardening series:

- academic identity verification does not treat name similarity alone as authorship proof;
- approval requires verified evidence and fails closed when required verification is unavailable or mismatched;
- normalization behavior is regression-locked and shared helpers were deduplicated without changing established semantics;
- the decision actor comes from the authenticated GitHub Actions boundary and is validated before persistence;
- decision history is append-only rather than overwritten;
- effective/current state is derived from the latest decision for a DOI while preserving prior decisions;
- approval publication state and decision audit history use rollback-safe persistence so a failed second write does not leave a partial approved state;
- the review UI fails closed when decision history cannot be loaded or parsed;
- end-to-end tests cover approve/reject decision integrity;
- academic JSON files used by the current persistence/review model are syntax-validated in CI;
- the Academic safety workflow gates changes to the protected academic paths covered by the workflow.

## Closure of prior audit findings

### ARI-01 — CLOSED

The earlier audit found that publication persistence could advance before decision-history persistence. The remediation introduced rollback-safe/atomic approval behavior with failure-injection regression coverage. A failed persistence operation must not leave a surviving partial approval state.

### ARI-02 — CLOSED

The earlier audit found that the review UI could continue with an empty decision map when decision history was unavailable. The remediation changed this behavior to fail closed and added regression coverage for unavailable/invalid decision history.

### CI JSON observation — CLOSED for the current persistence model

`data/academic-review.json` is now validated by the Academic safety workflow. The stale `data/academic.json` assumption was removed because that file is not part of the current repository persistence model.

## Residual operational caveats

This certification is a code/repository baseline certification, not a claim that every external GitHub repository setting is permanently enforced.

In particular:

- branch/ruleset configuration is an external repository control and should not be inferred solely from application code;
- authenticated actor assurance depends on the trusted GitHub Actions execution boundary remaining configured as designed;
- future changes to academic workflow paths, persistence files, identity rules, or decision semantics can invalidate this certification if they bypass or weaken the certified controls;
- third-party bibliographic source availability and correctness remain external dependencies; the application should continue to fail closed rather than manufacture identity certainty when evidence is insufficient.

These are operational/dependency boundaries rather than unresolved blockers in the certified v1 implementation.

## Freeze policy

After this certification is merged:

1. Treat `25587bd919e6656ba0058a2ae28ae101b52aad0f` as the pre-certification Academic Review v1 code baseline and the certification merge as its documentation seal.
2. Do not modify the frozen Academic Review behavior casually while developing unrelated features.
3. Any subsequent change affecting academic identity verification, review decisions, decision history, publication persistence, review UI integrity, or Academic safety workflow coverage must use a dedicated branch and pull request.
4. Academic safety tests must pass before such a change is merged.
5. Behavioral changes must include regression coverage demonstrating that the v1 integrity guarantees remain intact or explicitly document a new versioned contract.
6. If a future change intentionally alters a certified v1 invariant, create a new audit/certification baseline rather than silently treating this document as still current.

## Certification statement

At the baseline identified above, the previously identified freeze blockers are closed and the repository's Academic safety workflow passes on `main`. Subject to the operational caveats documented here, **Academic Review v1 is certified for freeze**.