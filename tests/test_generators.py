import os
import sys
import unittest

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "script")
sys.path.insert(0, SCRIPT_DIR)

from guide_generator import _batch_missing_tasks, _guide_exists  # noqa: E402
from insight_generator import _batch_missing_tasks as insight_tasks, _insight_exists  # noqa: E402


class GeneratorPathTest(unittest.TestCase):
    def test_guide_exists_single_md(self):
        self.assertTrue(_guide_exists("how-to-read-benchmarks"))

    def test_guide_not_exists_expand_japan(self):
        self.assertFalse(_guide_exists("guide_expand_001"))

    def test_insight_exists(self):
        self.assertTrue(_insight_exists("signup-one-fewer-step"))

    def test_batch_missing_skips_existing_guides(self):
        tasks = _batch_missing_tasks(10)
        ids = {t[0] for t in tasks}
        self.assertNotIn("how-to-read-benchmarks", ids)

    def test_batch_missing_insights_empty_when_all_built(self):
        """All rows in insights.csv currently have MD on disk."""
        tasks = insight_tasks(10)
        self.assertEqual(tasks, [])


if __name__ == "__main__":
    unittest.main()
