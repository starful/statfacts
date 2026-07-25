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

def _claude_md(prompt: str) -> str:
    """MD text via Claude CLI subscription (not Claude API)."""
    import sys
    from pathlib import Path
    _shared = Path(__file__).resolve().parents[2] / "shared"
    if str(_shared) not in sys.path:
        sys.path.insert(0, str(_shared))
    from site_llm import generate_md_text
    return generate_md_text(prompt)


from content_quality import (
    GUIDE_MIN_CHARS,
    QUALITY_PROMPT_RULES,
    is_blocked_guide_id,
)
from md_clean import prepare_guide_md
from topic_queue_csv import resolve as resolve_queue_csv


def _emit_pipeline_result(**kwargs):
    try:
        from generation_result import emit_generation_result

        emit_generation_result(**kwargs)
    except ImportError:
        pass

MODEL = "claude"  # via CLI
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
GUIDE_DIR = os.path.join(BASE_DIR, "app", "content", "guides")


def _guide_exists(guide_id: str) -> bool:
    return any(
        os.path.isfile(os.path.join(GUIDE_DIR, name))
        for name in (f"{guide_id}.md", f"{guide_id}_en.md")
    )


def generate_guide(guide_id: str, topic: str, keywords: str) -> bool:
    
    if is_blocked_guide_id(guide_id):
        print(f"⏭️ Blocked guide id: {guide_id}")
        return False

    print(f"🚀 [Guide AI] Generating guide: {topic}...")

    feedback = ""
    last_err: Exception | None = None
    for attempt in range(3):
        feedback_block = f"\n[FIX PREVIOUS FAILURE]\n{feedback}\n" if feedback else ""
        prompt = f"""
You are an editorial writer for StatFacts (statfacts.net), a site about effect-size benchmarks for product, business, sports, and health teams.

Write a practical English methodology guide — not travel content.

[Topic]
- Subject: {topic}
- SEO keywords: {keywords}

{QUALITY_PROMPT_RULES}
{feedback_block}
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
2. Use unique H2/H3 sections tailored to THIS topic (at least 3 H2s), bullets, and a short table if helpful.
3. Link concepts to reading StatFacts insight cards (effect ranges, confidence, sample_context).
4. Minimum {GUIDE_MIN_CHARS} characters.
5. End with related links to /guide/how-to-read-benchmarks and /tools/benchmark-calculator when relevant.

Tone: precise, no hype. Do not invent specific study citations — describe how to use benchmarks responsibly.
"""
        try:
            response_text = _claude_md(prompt)
            final_text = prepare_guide_md(
                response_text,
                guide_id=guide_id,
                fallback_title=topic,
                fallback_summary=topic,
            )
            os.makedirs(GUIDE_DIR, exist_ok=True)
            filename = f"{guide_id}.md"
            with open(os.path.join(GUIDE_DIR, filename), "w", encoding="utf-8") as f:
                f.write(final_text)
            print(f"✅ [Done] {filename}")
            return True
        except Exception as e:
            last_err = e
            feedback = str(e)
            print(f"⚠️  guide attempt {attempt + 1} failed: {e}")

    print(f"❌ [Failed] {guide_id}: {last_err}")
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
            if not guide_id or guide_id.startswith("#") or is_blocked_guide_id(guide_id):
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
        _emit_pipeline_result(step="guides", topics=len(tasks), generated=0, skipped=len(tasks))
        return 0
    if not tasks:
        print("✨ No new guides to generate.")
        _emit_pipeline_result(step="guides", topics=0, generated=0)
        return 0

    print(f"🔔 Starting generation for {len(tasks)} guide(s)...")
    ok = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(generate_guide, *t) for t in tasks]
        for fut in concurrent.futures.as_completed(futures):
            if fut.result():
                ok += 1
    failed = len(tasks) - ok
    _emit_pipeline_result(step="guides", topics=len(tasks), generated=ok, failed=failed)
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
