"""
StatFacts guide generator — English methodology guides from guides.csv.
Writes `app/content/guides/{id}.md` (single EN file, no _ko).
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

from md_clean import prepare_guide_md
from resolve_secrets import ensure_gemini_api_key
from topic_queue_csv import resolve as resolve_queue_csv

MODEL = "gemini-2.5-flash"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
GUIDE_DIR = os.path.join(BASE_DIR, "app", "content", "guides")


def _guide_exists(guide_id: str) -> bool:
    return any(
        os.path.isfile(os.path.join(GUIDE_DIR, name))
        for name in (f"{guide_id}.md", f"{guide_id}_en.md")
    )


def generate_guide(guide_id: str, topic: str, keywords: str) -> bool:
    if not ensure_gemini_api_key():
        print("❌ GEMINI_API_KEY is missing — set env, .env, or GCP Secret Manager (GEMINI_API_KEY)")
        return False

    try:
        from google import genai

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    except ImportError:
        print("❌ google-genai package required: pip install google-genai")
        return False

    print(f"🚀 [Guide AI] Generating guide: {topic}...")

    prompt = f"""
You are an editorial writer for StatFacts (statfacts.net), a site about effect-size benchmarks for product, business, sports, and health teams.

Write a practical English methodology guide — not travel content.

[Topic]
- Subject: {topic}
- SEO keywords: {keywords}

[Output format — STRICT]
Start with YAML frontmatter, then markdown body. No code fences.

---
lang: en
title: "Clear SEO title about {topic}"
summary: "Two-sentence summary on one line."
date: "{datetime.now().strftime('%Y-%m-%d')}"
---

[Body requirements]
1. Hook intro (2–3 sentences) for PMs, growth, or analysts.
2. Use H2/H3 sections, bullets, and a short table if helpful.
3. Link concepts to reading StatFacts insight cards (effect ranges, confidence, sample_context).
4. Minimum 2,500 characters.
5. End with "Related guides" linking to /guide/how-to-read-benchmarks and /tools/benchmark-calculator when relevant.

Tone: precise, no hype. Do not invent specific study citations — describe how to use benchmarks responsibly.
"""

    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        final_text = prepare_guide_md(response.text, guide_id=guide_id)
        os.makedirs(GUIDE_DIR, exist_ok=True)
        filename = f"{guide_id}.md"
        with open(os.path.join(GUIDE_DIR, filename), "w", encoding="utf-8") as f:
            f.write(final_text)
        print(f"✅ [Done] {filename}")
        return True
    except Exception as e:
        print(f"❌ [Failed] {guide_id}: {e}")
        return False


def _batch_missing_tasks(limit: int) -> list[tuple[str, str, str]]:
    csv_path = resolve_queue_csv("guides", os.path.join(SCRIPT_DIR, "csv", "guides.csv"))
    if not os.path.isfile(csv_path):
        print(f"❌ CSV not found: {csv_path}")
        return []

    tasks: list[tuple[str, str, str]] = []
    topics = 0
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if topics >= limit:
                break
            guide_id = (row.get("id") or "").strip()
            if not guide_id or guide_id.startswith("#"):
                continue
            if _guide_exists(guide_id):
                continue
            topic = (row.get("topic_en") or guide_id).strip()
            keywords = (row.get("keywords") or "").strip()
            tasks.append((guide_id, topic, keywords))
            topics += 1
    return tasks


def _run_tasks(tasks: list[tuple[str, str, str]], *, dry_run: bool) -> int:
    if dry_run:
        print(f"🔔 [dry-run] {len(tasks)} guide(s)")
        for gid, topic, _ in tasks:
            print(f"   {gid}.md — {topic}")
        return 0
    if not tasks:
        print("✨ No new guides to generate.")
        return 0

    print(f"🔔 Starting generation for {len(tasks)} guide(s)...")
    ok = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(generate_guide, *t) for t in tasks]
        for fut in concurrent.futures.as_completed(futures):
            if fut.result():
                ok += 1
    failed = len(tasks) - ok
    if failed:
        print(f"⚠️  {failed} guide(s) failed")
        return 1
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate StatFacts methodology guides.")
    parser.add_argument(
        "limit",
        nargs="?",
        type=int,
        default=3,
        help="Max CSV topics to fill per run (default 3).",
    )
    parser.add_argument(
        "--batch-missing",
        type=int,
        metavar="N",
        dest="batch_missing",
        help="Same as positional limit (okadmin hub).",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    limit = args.batch_missing if args.batch_missing is not None else args.limit
    tasks = _batch_missing_tasks(limit)
    return _run_tasks(tasks, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
