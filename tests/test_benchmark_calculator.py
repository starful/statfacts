import unittest

from app import app
from app.benchmark_calc import apply_benchmark, estimate_weeks, sample_size_per_variant


class BenchmarkCalcTest(unittest.TestCase):
    def test_relative_increase_range(self):
        r = apply_benchmark(22, 12, 18, unit="percent_relative", direction="increase")
        self.assertEqual(r["new_lo"], 24.64)
        self.assertEqual(r["new_hi"], 25.96)
        self.assertAlmostEqual(r["abs_lo"], 2.64)
        self.assertAlmostEqual(r["abs_hi"], 3.96)

    def test_percent_point_increase(self):
        r = apply_benchmark(30, 8, 8, unit="percent_point", direction="increase")
        self.assertEqual(r["new_lo"], 38.0)
        self.assertEqual(r["new_hi"], 38.0)
        self.assertEqual(r["abs_lo"], 8.0)

    def test_relative_decrease(self):
        r = apply_benchmark(40, 10, 20, unit="percent_relative", direction="decrease")
        self.assertEqual(r["new_lo"], 32.0)
        self.assertEqual(r["new_hi"], 36.0)

    def test_sample_size_absolute_mde(self):
        r = sample_size_per_variant(5, 1, mde_mode="absolute_pp", alpha=0.05, power=0.80)
        self.assertIsNotNone(r)
        assert r is not None
        self.assertGreaterEqual(r["per_variant"], 8000)
        self.assertLessEqual(r["per_variant"], 8200)
        self.assertEqual(r["total"], r["per_variant"] * 2)

    def test_sample_size_invalid_baseline(self):
        self.assertIsNone(sample_size_per_variant(0, 1))

    def test_estimate_weeks(self):
        self.assertAlmostEqual(estimate_weeks(10000, 5000), 2.0)


class BenchmarkCalculatorRouteTest(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_calculator_page_loads(self):
        resp = self.client.get("/tools/benchmark-calculator")
        self.assertEqual(resp.status_code, 200)
        body = resp.data
        self.assertIn(b"Benchmark calculator", body)
        self.assertIn(b"Apply benchmark", body)
        self.assertIn(b"A/B sample size", body)
        self.assertIn(b"benchmark_calculator.js", body)

    def test_calculator_prefill_query(self):
        resp = self.client.get(
            "/tools/benchmark-calculator"
            "?from=signup-one-fewer-step_en&min=12&max=18&unit=percent_relative"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'value="12"', resp.data)
        self.assertIn(b'value="18"', resp.data)

    def test_insight_detail_has_calculator_cta(self):
        resp = self.client.get("/insight/signup-one-fewer-step_en")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Plan with this benchmark", resp.data)
        self.assertIn(b"/tools/benchmark-calculator?", resp.data)

    def test_sitemap_includes_calculator(self):
        body = self.client.get("/sitemap.xml").get_data(as_text=True)
        self.assertIn("/tools/benchmark-calculator", body)


if __name__ == "__main__":
    unittest.main()
