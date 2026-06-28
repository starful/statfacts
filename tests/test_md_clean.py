import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "script"))

from md_clean import clean_md  # noqa: E402


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

    def test_preserves_valid_frontmatter(self):
        raw = "---\nid: foo\nlang: en\ntitle: Hi\n---\n\n## What changes\n"
        self.assertEqual(clean_md(raw), raw.strip())

    def test_strips_lone_delimiter_without_yaml(self):
        raw = "---\n\nIntro paragraph.\n\n## Section\n"
        out = clean_md(raw)
        self.assertFalse(out.startswith("---"))
        self.assertIn("Intro paragraph", out)

    def test_preserves_frontmatter_with_blank_line_after_opening(self):
        raw = "---\n\nid: foo\nlang: en\ntitle: Hi\n---\n\n## What changes\n"
        self.assertEqual(clean_md(raw), raw.strip())


if __name__ == "__main__":
    unittest.main()
