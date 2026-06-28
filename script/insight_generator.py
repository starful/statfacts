"""
StatFacts insight generator — creates `app/content/{id}_en.md` from insights.csv rows.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import os
import re
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from resolve_secrets import ensure_gemini_api_key

MODEL = "gemini-2.5-flash"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")
CSV_PATH = os.path.join(SCRIPT_DIR, "csv", "insights.csv")


def clean_ai_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    text = re.sub(r"^(##\s*)?yaml\n", "", text, flags=re.IGNORECASE)
    if "---" in text and not text.startswith("---"):
        text = "---" + text.split("---", 1)[1]
    return text.strip()


def _insight_path(insight_id: str) -> str:
    return os.path.join(CONTENT_DIR, f"{insight_id}_en.md")


def _insight_exists(insight_id: str) -> bool:
    base = insight_id.replace("_en", "").replace("_ko", "")
    return any(
        os.path.isfile(os.path.join(CONTENT_DIR, name))
        for name in (f"{base}_en.md", f"{base}.md")
    )


def _normalize_categories(raw: str) -> str:
    cats = [c.strip() for c in (raw or "").split(",") if c.strip()]
    return ", ".join(cats) if cats else "business"


def generate_insight(row: dict[str, str]) -> bool:
    if not ensure_gemini_api_key():
        print("❌ GEMINI_API_KEY is missing")
        return False

    try:
        from google import genai

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    except ImportError:
        print("❌ google-genai required: pip install google-genai")
        return False

    iid = (row.get("id") or "").strip()
    topic = (row.get("topic") or iid).strip()
    intervention = (row.get("intervention") or "").strip()
    outcome = (row.get("outcome") or "").strip()
    effect_min = (row.get("effect_min") or "").strip()
    effect_max = (row.get("effect_max") or effect_min).strip()
    effect_unit = (row.get("effect_unit") or "percent_relative").strip()
    categories = _normalize_categories(row.get("categories", ""))
    confidence = (row.get("confidence") or "estimate").strip()
    keywords = (row.get("keywords") or "").strip()

    print(f"🚀 [Insight AI] {topic}...")

    prompt = f"""
You are a StatFacts (statfacts.net) editor. Write one English insight article as markdown.

Use these CSV facts exactly in frontmatter (do not change effect_min/max or unit):
- id: {iid}
- intervention: {intervention}
- outcome: {outcome}
- effect_min: {effect_min}
- effect_max: {effect_max}
- effect_unit: {effect_unit}
- categories: [{categories}]
- confidence: {confidence}
- topic/keywords context: {topic} / {keywords}

[Output format — STRICT]
Start with YAML frontmatter then body. No markdown code fences.

Required frontmatter keys:
id, lang: en, title (question form), categories (yaml list), intervention, outcome,
effect_min, effect_max, effect_unit, effect_direction (increase or decrease),
sample_context (who/when this applies), confidence, date: "{datetime.now().strftime('%Y-%m-%d')}",
summary (one line), hook (punchy one line), thumbnail: "/static/images/{iid}.jpg",
image_prompt (one line for Imagen: editorial illustration, no text, no logos),
sources (list of 1–2 items with name and url — real organizations only, use plausible URLs)

Body sections (H2):
## What changes
## When this tends to work
## When to be careful
## Practical takeaway

Keep effect ranges consistent with frontmatter. Tone: concise, cite-style, no fabricated paper titles in body.
Minimum 900 characters in body.
"""

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        final_text = clean_ai_response(response.text)
        os.makedirs(CONTENT_DIR, exist_ok=True)
        out_path = _insight_path(iid)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(final_text)
        print(f"✅ [Done] {iid}_en.md")
        return True
    except Exception as e:
        print(f"❌ [Failed] {iid}: {e}")
        return False


def _batch_missing_tasks(limit: int) -> list[dict[str, str]]:
    if not os.path.isfile(CSV_PATH):
        print(f"❌ CSV not found: {CSV_PATH}")
        return []

    tasks: list[dict[str, str]] = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if len(tasks) >= limit:
                break
            iid = (row.get("id") or "").strip()
            if not iid or iid.startswith("#"):
                continue
            if _insight_exists(iid):
                continue
            if not (row.get("intervention") or "").strip():
                continue
            tasks.append(dict(row))
    return tasks


def _run_tasks(tasks: list[dict[str, str]], *, dry_run: bool) -> int:
    if dry_run:
        print(f"🔔 [dry-run] {len(tasks)} insight(s)")
        for row in tasks:
            print(f"   {row.get('id')}_en.md")
        return 0
    if not tasks:
        print("✨ No new insights to generate.")
        return 0

    print(f"🔔 Starting generation for {len(tasks)} insight(s)...")
    ok = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(generate_insight, row) for row in tasks]
        for fut in concurrent.futures.as_completed(futures):
            if fut.result():
                ok += 1
    failed = len(tasks) - ok
    if failed:
        print(f"⚠️  {failed} insight(s) failed")
        return 1
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate StatFacts insights from CSV.")
    parser.add_argument("limit", nargs="?", type=int, default=6)
    parser.add_argument("--batch-missing", type=int, metavar="N", dest="batch_missing")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    limit = args.batch_missing if args.batch_missing is not None else args.limit
    tasks = _batch_missing_tasks(limit)
    return _run_tasks(tasks, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
