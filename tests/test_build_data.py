import os
import tempfile
import unittest
from datetime import date, datetime, timedelta

from script.build_data import _insight_sort_key, _normalize_published


class NormalizePublishedTest(unittest.TestCase):
    def test_uses_max_of_frontmatter_and_mtime(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            path = tmp.name
        try:
            old = date.today() - timedelta(days=40)
            os.utime(path, (datetime.now().timestamp(), datetime.now().timestamp()))
            pub = _normalize_published(old.isoformat(), path)
            self.assertEqual(pub, date.today().isoformat())
        finally:
            os.unlink(path)

    def test_frontmatter_wins_when_newer_than_mtime(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            path = tmp.name
        try:
            future = date.today() + timedelta(days=1)
            old_mtime = (datetime.now() - timedelta(days=5)).timestamp()
            os.utime(path, (old_mtime, old_mtime))
            pub = _normalize_published(future.isoformat(), path)
            self.assertEqual(pub, future.isoformat())
        finally:
            os.unlink(path)


class InsightSortKeyTest(unittest.TestCase):
    def test_same_day_orders_by_mtime_then_id(self):
        day = "2026-07-05"
        newer = _insight_sort_key(day, 2000.0, "zebra-slug")
        older = _insight_sort_key(day, 1000.0, "alpha-slug")
        self.assertGreater(newer, older)

    def test_newer_date_wins_over_newer_mtime(self):
        newer_day = _insight_sort_key("2026-07-06", 1.0, "a")
        older_day = _insight_sort_key("2026-07-05", 9999.0, "z")
        self.assertGreater(newer_day, older_day)


if __name__ == "__main__":
    unittest.main()
