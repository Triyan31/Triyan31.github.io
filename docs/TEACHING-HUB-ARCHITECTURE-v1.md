# Teaching Hub V1 — Public Course Profile Contract

**Status:** Active baseline (TH-04 scope refinement)  
**Pilot course:** Business Intelligence

## 1. Purpose

Teaching Hub is the public teaching-portfolio layer of this website. Its purpose is to show which courses are taught, what each course broadly focuses on, how teaching is approached, and which relevant tools are used.

Teaching Hub is deliberately **not** an LMS, an RPS repository, or a public mirror of institutional academic administration.

## 2. Scope decision

The original TH-01 proposal allowed detailed outcomes, meeting plans, assessments, references, and separate course-content documents. That design was intentionally simplified before course content was published.

V1 does **not** require or publish:

- RPS files;
- CPL, CPMK, or Sub-CPMK structures;
- per-meeting plans;
- assessment weights or grading rules;
- downloadable lecture materials;
- student assignments or submissions;
- attendance, grades, feedback, or enrolment data.

Those items remain outside this public portfolio unless a later, explicit requirement changes the contract.

## 3. Public content model

The reusable course page may show only lightweight public-profile information:

- course title;
- course category/type;
- short public description;
- focus areas;
- teaching approach;
- relevant tools.

A course may be listed in the catalogue without a completed public profile. In that case the page should clearly state that the profile is still being prepared rather than inventing missing information.

## 4. URL model

Canonical V1 routes:

- `/teaching.html` — Teaching Hub catalogue;
- `/course.html?id=<course-id>` — reusable public course profile.

The query-string identifier keeps V1 compatible with GitHub Pages and avoids duplicated HTML pages.

## 5. Data contract

`data/teaching.json` remains the single lightweight public catalogue and profile source.

Required catalogue fields for a published course:

```json
{
  "id": "business-intelligence",
  "order": 1,
  "type": "DATA & DECISION",
  "title": "Business Intelligence",
  "description": "...",
  "published": true
}
```

An optional completed public profile uses:

```json
{
  "profile": {
    "focus_areas": ["..."],
    "teaching_approach": ["..."],
    "tools": ["..."]
  }
}
```

Each profile list must contain non-empty plain strings. Dynamic values are rendered as text, not injected as HTML.

V1 does not require `data/courses/<course-id>.json` files.

## 6. Moodle boundary

Moodle remains the system for operational learning activity, including:

- enrolment and authenticated course access;
- attendance;
- quizzes;
- assignments and submissions;
- grades and student-specific feedback;
- course files or learning materials that are distributed through the LMS.

Teaching Hub must not become a second Moodle.

## 7. Source and accuracy policy

Public course-profile text must be intentionally approved for publication. The site must not infer formal curriculum claims, learning outcomes, assessment rules, references, or tools that have not been established.

RPS documents may be consulted privately when useful, but V1 neither requires users to upload an RPS nor publishes an RPS file.

## 8. Security and privacy

- Only `published: true` catalogue entries are routable.
- Course IDs must match the approved slug format.
- Invalid, unknown, unpublished, or malformed catalogue state fails closed.
- Dynamic profile content uses DOM text nodes/`textContent`, never unsanitized `innerHTML`.
- No student identity, grade, submission, attendance, or other private learning data belongs in this contract.

## 9. Progressive publication

Business Intelligence is the first course with a completed public profile. Other published courses may remain catalogue-only until their profile information is intentionally prepared.

This is preferable to filling gaps with generated or assumed academic content.

## 10. V1 acceptance criteria

Teaching Hub V1 satisfies this refined contract when:

1. `teaching.html` lists valid published courses from `data/teaching.json`;
2. each published course resolves through the reusable `course.html?id=...` route;
3. a valid optional public profile renders focus areas, teaching approach, and tools;
4. catalogue-only courses show a clear profile-pending state;
5. invalid/unpublished routes fail closed;
6. no RPS upload or detailed LMS/academic-administration content is required;
7. regression tests and CI protect the contract.

This document replaces the more detailed TH-01 course-content proposal as the active Teaching Hub V1 scope.