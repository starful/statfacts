import json
import re
import unittest
from datetime import date
from pathlib import Path

from app import app


class ApiSmokeTest(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_api_insights_returns_list(self):
        response = self.client.get("/api/insights")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertIsInstance(payload, dict)

        list_key = next((k for k, v in payload.items() if isinstance(v, list)), None)
        self.assertIsNotNone(list_key)
        self.assertIn("last_updated", payload)
        self.assertGreater(len(payload[list_key]), 0)

    def test_insight_detail_page(self):
        response = self.client.get("/insight/signup-one-fewer-step_en")
        self.assertEqual(response.status_code, 200)
        body = response.data.lower()
        self.assertIn(b"signup", body)
        self.assertIn(b"share-bar", body)
        self.assertIn(b"copy link", body)
        self.assertNotIn(b"copy quote", body)
        self.assertIn(b"share-btn-x", body)
        self.assertIn(b"reaction-panel", body)
        self.assertIn(b"/social/signup-one-fewer-step.jpg", body)

    def test_reactions_api_returns_counts(self):
        response = self.client.get("/api/reactions/smoke-test-slug")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("likes", payload)
        self.assertIn("dislikes", payload)

    def test_robots_and_sitemap_exist(self):
        robots = self.client.get("/robots.txt")
        self.assertEqual(robots.status_code, 200)
        self.assertIn("Sitemap:", robots.get_data(as_text=True))

        sitemap = self.client.get("/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        body = sitemap.get_data(as_text=True)
        self.assertIn("<urlset", body)
        self.assertIn("<loc>", body)
        self.assertIn("/insight/", body)
        self.assertIn("<lastmod>", body)
        lastmods = re.findall(r"<lastmod>([^<]+)</lastmod>", body)
        self.assertGreater(len(set(lastmods)), 1)

    def test_sitemap_insight_lastmod_matches_published(self):
        data_path = Path(__file__).resolve().parents[1] / "app/static/json/insights_data.json"
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        sample = next(i for i in payload["insights"] if i.get("published"))
        insight_id = sample["id"]
        expected = sample["published"][:10]

        body = self.client.get("/sitemap.xml").get_data(as_text=True)
        pattern = rf"<loc>[^<]*/insight/{re.escape(insight_id)}</loc><lastmod>{expected}</lastmod>"
        self.assertRegex(body, pattern)

    def test_social_image_route(self):
        resp = self.client.get("/social/signup-one-fewer-step.jpg")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "image/jpeg")
        self.assertTrue(len(resp.data) > 1000)

    def test_option_b_card_routes(self):
        demo = self.client.get("/demo/cards")
        self.assertEqual(demo.status_code, 200)
        self.assertIn(b"Option B", demo.data)

        og = self.client.get("/og/insight/signup-one-fewer-step_en.png")
        self.assertEqual(og.status_code, 200)
        self.assertEqual(og.mimetype, "image/png")
        self.assertTrue(len(og.data) > 1000)

    def test_manifest_route_exists(self):
        manifest = self.client.get("/site.webmanifest")
        self.assertEqual(manifest.status_code, 200)
        self.assertIn("StatFacts", manifest.get_data(as_text=True))

    def test_homepage_shows_latest_insights(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.data
        self.assertIn(b"Latest insights", body)
        self.assertIn(b"insight-card", body)

    def test_category_landing_page(self):
        response = self.client.get("/category/ux")
        self.assertEqual(response.status_code, 200)
        body = response.data.lower()
        self.assertIn(b"ux", body)
        self.assertIn(b"benchmark", body)

    def test_homepage_has_featured_categories(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Explore by topic", response.data)
        self.assertIn(b"/category/ux", response.data)


if __name__ == "__main__":
    unittest.main()
