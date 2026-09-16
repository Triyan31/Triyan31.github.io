# Academic Review Dead/Duplicate Code Audit v1

## Scope

Conservative audit of the academic review surface after the identity-verification hardening merge. Scope inspected:

- `review.html`
- `review.js`
- `review.css`
- `scripts/review_academic.py`
- `scripts/sync_academic.py`
- `tests/test_academic_review.py`
- academic GitHub Actions/workflow references and generated review data paths

## Baseline findings

### 1. No proven removable dead feature path yet

The major review UI sections and selectors currently map to live markup/rendering paths. The review hero, policy panel, dashboard, evidence groups, decision controls/dialog, safe-decision flow, responsive rules, search/filter, spotlight, and authenticated workflow handoff are all referenced by the current page or renderer.

Result: **KEEP**. Do not delete these paths merely because some content is generated dynamically.

### 2. Apparent Python duplication is security-sensitive, not safe cleanup yet

`review_academic.py` has local helpers for JSON I/O, DOI normalization, name normalization, and exact registered-name checking while `sync_academic.py` contains related normalization/verification helpers.

This is genuine duplication pressure, but consolidating it now would change a trust-boundary path used by authenticated approval decisions. The regression tests currently exercise `review_academic.candidate_has_registered_name()` and `review_academic.doi_norm()` directly.

Result: **DEFER REFACTOR**. A shared helper module is reasonable later, but only in a dedicated refactor with unchanged behavior and regression coverage for both discovery and authenticated decision execution.

### 3. Fuzzy name matching is intentionally live

`sync_academic.person_matches()` is not obsolete after exact identity hardening. It remains the discovery-only signal used while generating candidate review records. Exact identity verification is separately enforced by `exact_person_match()` / exact registered-name evidence.

Result: **KEEP**. Removing fuzzy discovery would reduce candidate discovery and would conflate discovery semantics with verification semantics.

### 4. Review filter option injection is intentional runtime compatibility

`review.js` appends decision-state filter options (`needs_review`, `verified`, `rejected`) when they are absent from static `review.html`. This is not dead code under the current markup.

Result: **KEEP for v1**. A future markup cleanup may move these options into HTML, but doing both at once provides little value and adds avoidable UI churn.

### 5. `Keep for review` is UI-local, not repository persistence

The pending button only disables itself and changes its label in the current browser session. It does not persist a new decision. That matches the semantic meaning that an undecided candidate remains `needs_review` by default.

Result: **KEEP**, but document this distinction. Do not convert it into repository mutation without an explicit product decision.

### 6. Generated review data is not dead source code

`data/academic-review.json` and `data/academic-decisions.json` are runtime inputs to the public review console and authenticated decision history. Generated content may look redundant with source metadata but is part of the audit/review boundary.

Result: **KEEP**.

## Cleanup decision

No code is deleted in this audit PR because the audit did not establish a removal candidate with sufficiently low behavioral/security risk. This is deliberate: deleting code based only on visual similarity or duplicated helper names would be unsafe in the academic identity/approval path.

## Follow-up refactor candidate

The strongest future cleanup candidate is a small shared Python module for pure normalization helpers (DOI/name normalization and possibly JSON load/save), followed by imports from both academic scripts. Before that refactor:

1. preserve exact registered-name behavior;
2. preserve fuzzy discovery-only behavior;
3. preserve fail-closed approval behavior;
4. add equivalence tests for helper outputs;
5. run the complete academic safety workflow.

## Verdict

**PASS — no proven dead code should be removed at this stage.**

The repository does contain limited helper duplication, but the duplication crosses a security-sensitive identity/decision boundary. Treat it as a future controlled refactor, not dead-code deletion.
