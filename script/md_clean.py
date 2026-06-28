"""Normalize StatFacts markdown frontmatter for python-frontmatter."""
from __future__ import annotations

import re

_FM_START = re.compile(r"^(id|lang|title|summary):", re.IGNORECASE)
_BODY_START = re.compile(r"\n(?=## )")


def clean_md(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n", "", text)
    text = re.sub(r"\n```(?=\n## )", "", text)
    text = re.sub(r"\n```$", "", text)
    text = re.sub(r"^(##\s*)?yaml\n", "", text, flags=re.IGNORECASE)

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
