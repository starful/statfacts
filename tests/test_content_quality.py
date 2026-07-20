"""Tests for StatFacts content_quality gates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "script"))

from content_quality import (  # noqa: E402
    is_blocked_guide_id,
    quality_issues,
)


def test_blocked_guide_ids():
    assert is_blocked_guide_id("guide_seed_001")
    assert not is_blocked_guide_id("how-to-read-benchmarks")


def test_rejects_insight_template_skeleton():
    pad = "notes " * 200
    body = (
        f"## What changes\n{pad}\n"
        f"## When this tends to work\n{pad}\n"
        f"## When to be careful\n{pad}\n"
        f"## Practical takeaway\n{pad}\n"
    )
    issues = quality_issues(body, kind="insight")
    assert any(i.startswith("template_headings") for i in issues)


def test_accepts_unique_insight_headings():
    pad = "evidence and caveats for teams using benchmarks. " * 20
    body = (
        f"## Effect at a glance\n{pad}\n"
        f"## Who benefits most\n{pad}\n"
        f"## Measurement caveats\n{pad}\n"
    )
    assert quality_issues(body, kind="insight") == []
