import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "script"))

from md_clean import clean_md, load_post, prepare_insight_md  # noqa: E402


class CleanMdTest(unittest.TestCase):
    def test_wraps_bare_yaml_before_body(self):
        raw = "id: foo\nlang: en\ntitle: Hello\n\n## What changes\n\nBody."
        out = clean_md(raw)
        self.assertTrue(out.startswith("---\nid: foo"))
        self.assertIn("\n---\n\n## What changes", out)

    def test_strips_stray_fence_before_body(self):
        raw = "id: foo\nlang: en\ntitle: Hi\n```\n## What changes\n\nBody."
        out = clean_md(raw)
        self.assertNotIn("```", out)
        self.assertIn("title: Hi", out)

    def test_strips_fence_before_closing_delimiter(self):
        raw = """---
id: async-video-interview-completion
lang: en
title: Does async video help?
sources:
  - Name: SHRM
    Url: https://example.com
```
---

## What changes

Body text here with enough content."""
        out = clean_md(raw)
        self.assertNotIn("```", out)
        post = load_post(out)
        self.assertEqual(post["title"], "Does async video help?")
        self.assertEqual(post["sources"][0]["name"], "SHRM")

    def test_preserves_valid_frontmatter(self):
        raw = "---\nid: foo\nlang: en\ntitle: Hi\n---\n\n## What changes\n"
        self.assertEqual(clean_md(raw), raw.strip())

    def test_strips_lone_delimiter_without_yaml(self):
        raw = "---\n\nIntro paragraph.\n\n## Section\n"
        out = clean_md(raw)
        self.assertFalse(out.startswith("---"))
        self.assertIn("Intro paragraph", out)

    def test_prepare_insight_requires_sections(self):
        raw = "---\nid: x\nlang: en\ntitle: Q?\nintervention: a\noutcome: b\nimage_prompt: test prompt here\n---\n\n## What changes\n\nok"
        out = prepare_insight_md(raw, insight_id="x")
        self.assertIn("title: Q?", out)

    def test_repairs_stray_bullet_in_frontmatter(self):
        from md_clean import prepare_guide_md

        raw = (
            "---\nlang: en\ntitle: Test guide\nsummary: Summary line here.\n"
            "date: 2026-06-29\n* Related guides link\n---\n\n## Intro\n"
        ) + ("body " * 80)
        out = prepare_guide_md(raw, guide_id="test-guide")
        post = load_post(out)
        self.assertEqual(post["title"], "Test guide")

    def test_quotes_colon_in_scalar(self):
        from md_clean import prepare_guide_md

        raw = (
            "---\nlang: en\n"
            "title: Funnel steps: definitions for teams\n"
            "summary: Summary line here.\n"
            "date: 2026-06-29\n---\n\n## Intro\n"
        ) + ("body " * 80)
        out = prepare_guide_md(raw, guide_id="funnel")
        post = load_post(out)
        self.assertIn(":", post["title"])

    def test_guide_fills_missing_title_from_fallback(self):
        from md_clean import prepare_guide_md

        raw = (
            "---\nlang: en\nsummary: Short.\n"
            "date: 2026-06-29\n---\n\n## Intro section\n"
        ) + ("body " * 80)
        out = prepare_guide_md(
            raw,
            guide_id="funnel-step-definitions",
            fallback_title="Defining funnel steps consistently across teams",
            fallback_summary="Defining funnel steps consistently across teams",
        )
        post = load_post(out)
        self.assertEqual(post["title"], "Defining funnel steps consistently across teams")
        self.assertGreaterEqual(len(post["summary"]), 10)


if __name__ == "__main__":
    unittest.main()
