import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEACHING = ROOT / "data" / "teaching.json"
COURSE_HTML = ROOT / "course.html"
COURSE_JS = ROOT / "course.js"
TEACHING_JS = ROOT / "teaching.js"


class TeachingCourseContractTests(unittest.TestCase):
    def test_catalogue_schema_and_published_course_ids_are_valid(self):
        data = json.loads(TEACHING.read_text(encoding="utf-8"))
        self.assertEqual(data.get("schema_version"), 1)
        courses = data.get("courses")
        self.assertIsInstance(courses, list)
        published = [course for course in courses if course.get("published") is True]
        self.assertTrue(published)
        ids = [course["id"] for course in published]
        self.assertEqual(len(ids), len(set(ids)))
        for course in published:
            self.assertRegex(course["id"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertIsInstance(course.get("order"), int)
            self.assertTrue(course.get("type", "").strip())
            self.assertTrue(course.get("title", "").strip())
            self.assertTrue(course.get("description", "").strip())

    def test_business_intelligence_has_public_profile_only(self):
        data = json.loads(TEACHING.read_text(encoding="utf-8"))
        bi = next(course for course in data["courses"] if course["id"] == "business-intelligence")
        profile = bi.get("profile")
        self.assertIsInstance(profile, dict)
        for key in ("focus_areas", "teaching_approach", "tools"):
            self.assertIsInstance(profile.get(key), list)
            self.assertTrue(profile[key])
            self.assertTrue(all(isinstance(item, str) and item.strip() for item in profile[key]))
        serialized = json.dumps(bi).lower()
        for forbidden in ("rps", "cpmk", "sub-cpmk", "grade", "attendance", "submission"):
            self.assertNotIn(forbidden, serialized)

    def test_catalogue_links_to_reusable_course_route(self):
        source = TEACHING_JS.read_text(encoding="utf-8")
        self.assertIn("./course.html?id=", source)
        self.assertIn("encodeURIComponent(course.id)", source)

    def test_course_page_loads_catalogue_and_has_fail_closed_state(self):
        html = COURSE_HTML.read_text(encoding="utf-8")
        source = COURSE_JS.read_text(encoding="utf-8")
        self.assertIn('id="coursePage" hidden', html)
        self.assertIn('id="courseError"', html)
        self.assertIn("./data/teaching.json", source)
        self.assertIn("failClosed", source)
        self.assertIn("course.published === true", source)
        self.assertIn("item.id === requestedId", source)

    def test_course_page_is_portfolio_not_lms_or_rps_repository(self):
        html = COURSE_HTML.read_text(encoding="utf-8")
        self.assertIn("What I teach and how I approach it.", html)
        self.assertIn("not a replacement for Moodle", html)
        self.assertIn("RPS documents", html)
        self.assertNotIn("Learning outcomes", html)
        self.assertNotIn("Meeting plan", html)
        self.assertNotIn("Assessment map", html)

    def test_dynamic_catalogue_content_uses_text_content(self):
        source = COURSE_JS.read_text(encoding="utf-8")
        self.assertIn("type.textContent = course.type", source)
        self.assertIn("title.textContent = course.title", source)
        self.assertIn("description.textContent = course.description", source)
        self.assertIn("li.textContent = item", source)
        self.assertNotIn("innerHTML", source)


if __name__ == "__main__":
    unittest.main()
