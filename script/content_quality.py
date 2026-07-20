"""Quality gates for StatFacts insight/guide generation.

Prevents repeating the fixed four-H2 template batch and thin bodies.
"""

from __future__ import annotations

import re

BLOCKED_GUIDE_IDS = frozenset(
    {
        "guide_seed_001",
        "guide_seed_002",
        "guide_seed_003",
    }
)
BLOCKED_GUIDE_ID_PREFIXES = ("guide_seed_", "guide_expand_")

BLOCKED_INSIGHT_IDS: frozenset[str] = frozenset()
BLOCKED_INSIGHT_ID_PREFIXES = ("insight_seed_",)

# The mass-produced insight skeleton we are retiring from prompts.
FORBIDDEN_HEADINGS = frozenset(
    {
        "what changes",
        "when this tends to work",
        "when to be careful",
        "practical takeaway",
        "who this guide is for",
        "how to compare your options",
        "recommended decision process",
        "common mistakes to avoid",
        "final checklist",
    }
)

BANNED_PHRASES = (
    "definitive guide",
    "game-changing",
    "unlock the secrets",
    "in today's fast-paced",
    "as an expert",
)

INSIGHT_MIN_CHARS = 1800
GUIDE_MIN_CHARS = 3500
MIN_H2 = 3

QUALITY_PROMPT_RULES = """
Quality rules (mandatory):
- Write specifically about THIS intervention/outcome. No interchangeable filler.
- Do NOT use these template H2 titles: "What Changes", "When This Tends To Work",
  "When To Be Careful", "Practical Takeaway", "Who This Guide Is For",
  "Final Checklist".
- Invent unique ## headings that fit THIS topic (at least 3).
- Keep effect ranges consistent with provided frontmatter facts.
- Do not invent paper titles or fake citations.
- Raw Markdown only. No code fences.
""".strip()


def is_blocked_guide_id(topic_id: str) -> bool:
    tid = (topic_id or "").strip().lower()
    if not tid:
        return True
    if tid in BLOCKED_GUIDE_IDS:
        return True
    return any(tid.startswith(p) for p in BLOCKED_GUIDE_ID_PREFIXES)


def is_blocked_insight_id(insight_id: str) -> bool:
    iid = (insight_id or "").strip().lower()
    if not iid:
        return True
    if iid in BLOCKED_INSIGHT_IDS:
        return True
    return any(iid.startswith(p) for p in BLOCKED_INSIGHT_ID_PREFIXES)


def extract_h2_headings(body: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", body or "", re.M)]


def find_banned_phrases(text: str) -> list[str]:
    low = (text or "").lower()
    return [p for p in BANNED_PHRASES if p in low]


def quality_issues(
    body: str,
    *,
    kind: str = "insight",
    min_chars: int | None = None,
) -> list[str]:
    text = (body or "").strip()
    issues: list[str] = []
    floor = min_chars
    if floor is None:
        floor = INSIGHT_MIN_CHARS if kind == "insight" else GUIDE_MIN_CHARS

    if len(text) < floor:
        issues.append(f"too_short:{len(text)}<{floor}")

    headings = [h.lower() for h in extract_h2_headings(text)]
    if len(headings) < MIN_H2:
        issues.append(f"too_few_sections:{len(headings)}")

    banned_heads = [h for h in headings if h in FORBIDDEN_HEADINGS]
    # Insights used to force all four template headings — reject if most are present.
    if kind == "insight" and len(banned_heads) >= 3:
        issues.append(f"template_headings:{', '.join(banned_heads[:4])}")
    elif kind == "guide" and len(banned_heads) >= 2:
        issues.append(f"template_headings:{', '.join(banned_heads[:4])}")

    banned = find_banned_phrases(text)
    if banned:
        issues.append(f"banned_phrases:{', '.join(banned[:3])}")

    return issues


def assert_quality(body: str, *, kind: str = "insight", **kwargs) -> None:
    issues = quality_issues(body, kind=kind, **kwargs)
    if issues:
        raise ValueError("; ".join(issues))
