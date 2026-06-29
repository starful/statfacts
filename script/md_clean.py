"""Normalize StatFacts markdown frontmatter for python-frontmatter."""
from __future__ import annotations

import re
from datetime import datetime

import frontmatter

_FM_START = re.compile(r"^(id|lang|title|summary):", re.IGNORECASE)
_BODY_START = re.compile(r"\n(?=## )")
_FM_KV = re.compile(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$")
_FM_LIST_ITEM = re.compile(r"^-\s+")


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


def _has_yaml_keys(block: str) -> bool:
    return bool(re.search(r"^[A-Za-z0-9_.-]+\s*:", block, re.MULTILINE))


def clean_md(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    text = re.sub(r"^(##\s*)?yaml\n", "", text, flags=re.IGNORECASE)
    text = _normalize_source_keys(text)
    text = _strip_stray_fences(text)

    if text.startswith("---"):
        parts = _split_delimited(text)
        if parts is not None and _has_yaml_keys(parts[0]):
            return text.strip()
        rest = re.sub(r"^---\s*\n+", "", text, count=1)
        if _FM_START.search(rest.lstrip()) or _has_yaml_keys(rest.split("---", 1)[0]):
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


def _quote_yaml_scalar(val: str) -> str:
    val = val.strip()
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val
    escaped = val.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _needs_quoting(val: str) -> bool:
    val = val.strip()
    if not val:
        return False
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return False
    if val.startswith("[") or val.startswith("{"):
        return False
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", val):
        return False
    if ":" in val:
        return True
    if val and val[0] in "*&!#@`|>":
        return True
    if val.lower() in ("yes", "no", "true", "false", "null", "~"):
        return True
    return False


def _repair_fm_line(line: str) -> str:
    if not line.strip() or line.strip().startswith("#"):
        return line

    indent = line[: len(line) - len(line.lstrip())]
    stripped = line.lstrip()

    # Markdown bullets leaked into frontmatter (* triggers YAML alias parse errors).
    if stripped.startswith("*"):
        return f"{indent}# {stripped}"

    m = _FM_KV.match(stripped)
    if m:
        key, val = m.group(1), m.group(2)
        if _needs_quoting(val):
            return f"{indent}{key}: {_quote_yaml_scalar(val)}"
        return line

    if _FM_LIST_ITEM.match(stripped):
        rest = stripped[1:].strip()
        m2 = _FM_KV.match(rest)
        if m2:
            key, val = m2.group(1), m2.group(2)
            if _needs_quoting(val):
                return f"{indent}- {key}: {_quote_yaml_scalar(val)}"
            return line
        if _needs_quoting(rest):
            return f"{indent}- {_quote_yaml_scalar(rest)}"

    return line


def _repair_frontmatter_block(fm: str) -> str:
    return "\n".join(_repair_fm_line(line) for line in fm.splitlines())


def _split_delimited(text: str) -> tuple[str, str] | None:
    if not text.startswith("---"):
        return None
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not match:
        return None
    return match.group(1), match.group(2)


def _rejoin_frontmatter(fm_inner: str, body: str) -> str:
    return f"---\n{fm_inner.rstrip()}\n---\n\n{body.lstrip()}"


def _repair_frontmatter_text(text: str) -> str:
    parts = _split_delimited(text)
    if parts is not None:
        fm_inner, body = parts
        return _rejoin_frontmatter(_repair_frontmatter_block(fm_inner), body)

    if _FM_START.match(text):
        split = _BODY_START.split(text, maxsplit=1)
        if len(split) == 2:
            fm_inner, body = split[0].strip(), split[1]
            return _rejoin_frontmatter(_repair_frontmatter_block(fm_inner), body)

    return text


def _loads_post(text: str, *, max_attempts: int = 3):
    current = text
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return frontmatter.loads(current), current
        except Exception as exc:
            last_err = exc
            if attempt + 1 >= max_attempts:
                break
            current = _repair_frontmatter_text(current)
    assert last_err is not None
    raise last_err


def _first_heading(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        m = re.match(r"^#+\s+(.+)", stripped)
        if m:
            return m.group(1).strip()
    return ""


def _body_excerpt(body: str, *, limit: int = 240) -> str:
    text = re.sub(r"^#+\s+", "", body, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit].strip()


def _render_post(post) -> str:
    out = frontmatter.dumps(post)
    return out if out.endswith("\n") else out + "\n"


def _fill_guide_metadata(
    post,
    *,
    guide_id: str = "",
    fallback_title: str = "",
    fallback_summary: str = "",
) -> None:
    body = str(post.content or "")
    title = str(post.get("title") or "").strip()
    if not title or title == "Untitled":
        post["title"] = fallback_title or _first_heading(body) or guide_id or "Guide"
    if not str(post.get("lang") or "").strip():
        post["lang"] = "en"
    summary = str(post.get("summary") or "").strip()
    if len(summary) < 10:
        post["summary"] = (
            fallback_summary
            if len(fallback_summary) >= 10
            else _body_excerpt(body) or str(post.get("title") or fallback_title or guide_id)
        )
    if not str(post.get("date") or "").strip():
        post["date"] = datetime.now().strftime("%Y-%m-%d")


def _fill_insight_metadata(
    post,
    *,
    insight_id: str = "",
    fallback_title: str = "",
    fallback_intervention: str = "",
    fallback_outcome: str = "",
    fallback_summary: str = "",
    fallback_image_prompt: str = "",
) -> None:
    body = str(post.content or "")
    if insight_id and not str(post.get("id") or "").strip():
        post["id"] = insight_id
    if not str(post.get("lang") or "").strip():
        post["lang"] = "en"
    title = str(post.get("title") or "").strip()
    if not title or title == "Untitled":
        post["title"] = fallback_title or _first_heading(body) or insight_id or "Insight"
    if not str(post.get("intervention") or "").strip():
        post["intervention"] = fallback_intervention or str(post.get("title") or "")
    if not str(post.get("outcome") or "").strip():
        post["outcome"] = fallback_outcome or "Key outcome metric"
    summary = str(post.get("summary") or "").strip()
    if len(summary) < 5:
        post["summary"] = fallback_summary if fallback_summary else _body_excerpt(body, limit=160)
    prompt = str(post.get("image_prompt") or "").strip()
    if len(prompt) < 10:
        topic = str(post.get("title") or fallback_title or insight_id)
        post["image_prompt"] = fallback_image_prompt or (
            f"Editorial illustration about {topic}, no text, no logos"
        )
    if not str(post.get("date") or "").strip():
        post["date"] = datetime.now().strftime("%Y-%m-%d")


def load_post(raw: str):
    """Parse markdown after normalization; raises on invalid frontmatter."""
    post, _ = _loads_post(clean_md(raw))
    return post


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


def prepare_insight_md(
    raw: str,
    *,
    insight_id: str,
    fallback_title: str = "",
    fallback_intervention: str = "",
    fallback_outcome: str = "",
    fallback_summary: str = "",
    fallback_image_prompt: str = "",
) -> str:
    cleaned = clean_md(raw)
    post, _ = _loads_post(cleaned)
    _fill_insight_metadata(
        post,
        insight_id=insight_id,
        fallback_title=fallback_title,
        fallback_intervention=fallback_intervention,
        fallback_outcome=fallback_outcome,
        fallback_summary=fallback_summary,
        fallback_image_prompt=fallback_image_prompt,
    )
    validate_insight_post(post, insight_id=insight_id)
    return _render_post(post)


def prepare_guide_md(
    raw: str,
    *,
    guide_id: str,
    fallback_title: str = "",
    fallback_summary: str = "",
) -> str:
    cleaned = clean_md(raw)
    post, _ = _loads_post(cleaned)
    _fill_guide_metadata(
        post,
        guide_id=guide_id,
        fallback_title=fallback_title,
        fallback_summary=fallback_summary,
    )
    validate_guide_post(post, guide_id=guide_id)
    return _render_post(post)
