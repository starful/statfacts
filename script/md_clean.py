"""Normalize StatFacts markdown frontmatter for python-frontmatter."""
from __future__ import annotations

import re

import frontmatter

_FM_START = re.compile(r"^(id|lang|title|summary):", re.IGNORECASE)
_BODY_START = re.compile(r"\n(?=## )")


def _normalize_source_keys(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        line = re.sub(r"^(\s*-\s*)Name:", r"\1name:", line, flags=re.IGNORECASE)
        line = re.sub(r"^(\s+)Url:", r"\1url:", line, flags=re.IGNORECASE)
        lines.append(line)
    return "\n".join(lines)


def _strip_stray_fences(text: str) -> str:
    parts = _BODY_START.split(text, maxsplit=1)
    head = "\n".join(ln for ln in parts[0].splitlines() if ln.strip() != "```")
    head = re.sub(r"\n---\s*\n+---", "\n---", head)
    if len(parts) == 2:
        return head.rstrip() + "\n\n" + parts[1].lstrip()
    return head.rstrip()


def clean_md(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    text = re.sub(r"^(##\s*)?yaml\n", "", text, flags=re.IGNORECASE)
    text = _normalize_source_keys(text)
    text = _strip_stray_fences(text)

    if text.startswith("---"):
        rest = re.sub(r"^---\s*\n+", "", text, count=1)
        if _FM_START.search(rest.lstrip()):
            return text.strip()
        text = rest.lstrip()

    if "---" in text and not text.startswith("---"):
        return ("---" + text.split("---", 1)[1]).strip()

    if _FM_START.match(text):
        parts = _BODY_START.split(text, maxsplit=1)
        if len(parts) == 2:
            fm, body = parts[0].strip(), parts[1].strip()
            return f"---\n{fm}\n---\n\n{body}"
        return f"---\n{text.strip()}\n---\n"

    return text.strip()


def load_post(raw: str):
    """Parse markdown after normalization; raises on invalid frontmatter."""
    return frontmatter.loads(clean_md(raw))


def validate_insight_post(post, *, insight_id: str = "") -> None:
    title = str(post.get("title", "")).strip()
    if not title or title == "Untitled":
        raise ValueError(f"{insight_id or post.get('id')}: missing title")
    prompt = str(post.get("image_prompt", "")).strip()
    if len(prompt) < 10:
        raise ValueError(f"{insight_id or post.get('id')}: missing image_prompt")
    if not str(post.get("intervention", "")).strip():
        raise ValueError(f"{insight_id or post.get('id')}: missing intervention")
    body = str(post.content or "").strip()
    if "## What changes" not in body:
        raise ValueError(f"{insight_id or post.get('id')}: missing body sections")


def validate_guide_post(post, *, guide_id: str = "") -> None:
    title = str(post.get("title", "")).strip()
    if not title or title == "Untitled":
        raise ValueError(f"{guide_id or 'guide'}: missing title")
    summary = str(post.get("summary", "")).strip()
    if len(summary) < 10:
        raise ValueError(f"{guide_id or 'guide'}: missing summary")
    if len(str(post.content or "").strip()) < 200:
        raise ValueError(f"{guide_id or 'guide'}: body too short")


def prepare_insight_md(raw: str, *, insight_id: str) -> str:
    cleaned = clean_md(raw)
    post = frontmatter.loads(cleaned)
    validate_insight_post(post, insight_id=insight_id)
    return cleaned if cleaned.endswith("\n") else cleaned + "\n"


def prepare_guide_md(raw: str, *, guide_id: str) -> str:
    cleaned = clean_md(raw)
    post = frontmatter.loads(cleaned)
    validate_guide_post(post, guide_id=guide_id)
    return cleaned if cleaned.endswith("\n") else cleaned + "\n"
