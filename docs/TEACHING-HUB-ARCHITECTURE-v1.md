# Teaching Hub V1 — Architecture & Data Contract

**Status:** Proposed baseline (TH-01)
**Pilot course:** Business Intelligence

## 1. Purpose

Teaching Hub is the public learning layer of this portfolio. It publishes course-level outcomes, meeting plans, learning materials, assessments, and references in a form suitable for classroom support and independent learning.

It is **not** an LMS and must not duplicate Moodle responsibilities such as enrolment, private student data, submissions, grades, attendance, quizzes, or authenticated learning activity.

## 2. Design principles

1. **Outcome-first** — course and meeting content begins with intended learning outcomes rather than a list of files.
2. **Reusable** — all courses use one data contract and one page system.
3. **Public-safe** — only material intended for public access is represented.
4. **Source-aware** — references remain explicit; the site must not invent academic claims or references.
5. **Progressive** — a course may be published before every meeting is complete.
6. **Moodle boundary** — private/transactional learning activity remains in the institutional LMS.
7. **Static-site compatible** — V1 uses versioned JSON and client-side rendering; no backend is required.

## 3. URL model

Canonical V1 routes:

- `/teaching.html` — Teaching Hub index
- `/course.html?id=business-intelligence` — reusable course page

The query-string course identifier is deliberate for V1: it works on GitHub Pages without routing infrastructure and avoids four duplicated HTML implementations. A later version may adopt pretty URLs if deployment changes.

## 4. Data ownership

### `data/teaching.json`

Course catalogue only. It controls ordering, publication state, short descriptions, and discovery metadata. It must remain lightweight.

### `data/courses/<course-id>.json`

One public course document per course. The file is the canonical public content source for the reusable course page.

V1 pilot:

`data/courses/business-intelligence.json`

## 5. Course document contract

Required top-level fields:

```json
{
  "schema_version": 1,
  "id": "business-intelligence",
  "title": "Business Intelligence",
  "type": "DATA & DECISION",
  "summary": "...",
  "published": true,
  "outcomes": [],
  "meetings": [],
  "assessment": [],
  "references": []
}
```

### `outcomes[]`

Public course-level learning outcomes. V1 intentionally uses the neutral key `outcomes`; formal CPL/CPMK/Sub-CPMK codes should only be added when they are sourced from the approved curriculum/RPS rather than inferred by the website.

```json
{
  "id": "outcome-01",
  "label": "Course outcome",
  "text": "...",
  "source": "RPS"
}
```

### `meetings[]`

```json
{
  "number": 1,
  "title": "...",
  "summary": "...",
  "outcomes": ["outcome-01"],
  "topics": ["..."],
  "materials": [],
  "assessment_ids": ["assessment-01"],
  "published": true
}
```

A meeting may be unpublished while preparation is incomplete. The UI must not expose unpublished meetings.

### `materials[]`

```json
{
  "type": "slides",
  "title": "...",
  "url": "...",
  "public": true
}
```

Allowed V1 material types: `slides`, `reading`, `video`, `dataset`, `exercise`, `external`.

Only `public: true` materials may be rendered.

### `assessment[]`

```json
{
  "id": "assessment-01",
  "title": "...",
  "type": "formative",
  "description": "...",
  "outcomes": ["outcome-01"],
  "submission": "moodle"
}
```

Allowed V1 `type`: `diagnostic`, `formative`, `summative`.

`submission` is descriptive only. V1 supports `moodle`, `classroom`, `none`, or a public URL. Teaching Hub must not collect student submissions.

### `references[]`

```json
{
  "id": "ref-01",
  "type": "book",
  "citation": "...",
  "url": null
}
```

References must be real sources used for the course. A URL is optional; citation text is required. Do not fabricate bibliographic metadata to make an entry look complete.

## 6. Rendering contract

`teaching.html` reads `data/teaching.json` and renders only courses where `published === true`.

`course.html`:

1. reads and validates the `id` query parameter;
2. accepts only a conservative slug (`a-z`, `0-9`, `-`);
3. verifies that the course exists and is published in the catalogue;
4. fetches the matching course JSON;
5. verifies `schema_version === 1`, matching `id`, and `published === true`;
6. renders only published meetings and public materials;
7. fails closed with a clear unavailable state if catalogue/data loading or validation fails.

No course ID may be converted into an arbitrary fetch path without slug validation and catalogue membership checking.

## 7. UI information architecture

Teaching Hub index:

- Intro / purpose
- Published course cards
- Teaching philosophy: outcome → activity → assessment → reflection
- Moodle boundary note

Course page:

- Course identity and summary
- Learning outcomes
- Meeting roadmap
- Assessment map
- References
- LMS boundary / submission notice

The page should visually inherit the existing Academic × Technology portfolio rather than introduce a separate LMS-like visual system.

## 8. OBE boundary

The site may visualize alignment between outcomes, meetings, and assessments. It must **not** claim formal OBE compliance merely because these fields exist. Formal CPL/CPMK/Sub-CPMK mappings, rubrics, and attainment rules require approved academic source documents.

This distinction prevents the UI architecture from silently becoming an academic policy source.

## 9. Privacy and security boundary

Never publish:

- student names, identifiers, attendance, grades, submissions, or analytics;
- Moodle enrolment or authentication data;
- unpublished institutional documents;
- answer keys intended to remain restricted;
- credentials, tokens, private API endpoints, or operational configuration.

All external links rendered from course data must use safe link handling (`rel="noreferrer"` for new tabs). Dynamic text must be inserted as text, not unsanitized HTML.

## 10. V1 delivery sequence

- **TH-01** — architecture and data contract (this baseline)
- **TH-02** — Teaching Hub index and catalogue rendering
- **TH-03** — reusable course page + validation/fail-closed behavior
- **TH-04** — Business Intelligence pilot content from approved course sources
- **TH-05** — tests, accessibility, responsive verification, and V1 freeze
- **TH-06+** — migrate remaining courses using the frozen contract

## 11. TH-01 acceptance criteria

TH-01 is complete when:

- public Teaching Hub scope and Moodle boundary are explicit;
- URL strategy is GitHub Pages compatible;
- catalogue vs course-detail ownership is unambiguous;
- outcomes, meetings, materials, assessments, and references have a defined V1 contract;
- privacy, path validation, public-material filtering, and fail-closed rules are explicit;
- formal OBE claims are not inferred from UI/data structure;
- Business Intelligence is designated as the pilot without inventing its academic content.

No production UI change is required in TH-01. This is intentional: the contract should be reviewed before frontend implementation begins.
