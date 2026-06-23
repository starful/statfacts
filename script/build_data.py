"""
StatFacts data builder.
- Reads `app/content/*.md` (excluding guides/) and builds insights_data.json.
"""
import os
import json
import re
import importlib.util
import frontmatter
from datetime import datetime, date

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
IMAGES_DIR  = os.path.join(BASE_DIR, 'app', 'static', 'images')
OUTPUT_PATH = os.path.join(BASE_DIR, 'app', 'static', 'json', 'insights_data.json')


def _load_data_key() -> str:
    config_path = os.path.join(BASE_DIR, "app", "config.py")
    default_key = "insights"
    if not os.path.exists(config_path):
        return default_key
    try:
        spec = importlib.util.spec_from_file_location("statfacts_config", config_path)
        if spec is None or spec.loader is None:
            return default_key
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        site_config = getattr(module, "SITE_CONFIG", {})
        return str(site_config.get("data_key", default_key))
    except Exception:
        return default_key


def clean_md(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    text = re.sub(r'^(##\s*)?yaml\n', '', text, flags=re.IGNORECASE)
    if '---' in text and not text.startswith('---'):
        text = '---' + text.split('---', 1)[1]
    return text


def _format_effect(post) -> str:
    effect_min = post.get('effect_min')
    effect_max = post.get('effect_max')
    unit = str(post.get('effect_unit', 'percent_relative'))
    direction = str(post.get('effect_direction', 'increase'))

    if effect_min is None and effect_max is None:
        return str(post.get('effect_label', ''))

    try:
        lo = float(effect_min) if effect_min is not None else None
        hi = float(effect_max) if effect_max is not None else None
    except (TypeError, ValueError):
        return str(post.get('effect_label', ''))

    sign = '+' if direction != 'decrease' else '-'
    suffix = '%' if 'percent' in unit else ''

    if lo is not None and hi is not None and lo != hi:
        return f"{sign}{lo:g}–{hi:g}{suffix}"
    val = hi if hi is not None else lo
    return f"{sign}{val:g}{suffix}"


def _normalize_published(raw: str, fpath: str) -> str:
    """Return valid YYYY-MM-DD; fall back to file mtime if frontmatter is invalid."""
    s = str(raw or "").strip()[:10]
    if s:
        try:
            return date.fromisoformat(s).isoformat()
        except ValueError:
            pass
    try:
        return datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d")
    except OSError:
        return datetime.now().strftime("%Y-%m-%d")


def main():
    print("🔨 Building insights_data.json ...")
    insights = []
    data_key = _load_data_key()

    if not os.path.exists(CONTENT_DIR):
        print("❌ content directory not found")
        return

    for filename in sorted(os.listdir(CONTENT_DIR)):
        if not filename.endswith('.md'):
            continue

        fpath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                raw = f.read()

            post = frontmatter.loads(clean_md(raw))

            cats = post.get('categories', [])
            if isinstance(cats, str):
                cats = [c.strip() for c in cats.split(',')]

            summary = str(post.get('summary', ''))
            if not summary or len(summary) < 10:
                clean_body = re.sub(r'[#*`\-]', '', post.content).strip()
                summary = clean_body[:180].replace('\n', ' ') + '...'

            item_id = filename.replace('.md', '')
            slug = str(post.get('id', item_id)).replace('_en', '').replace('_ko', '')

            thumbnail = str(post.get('thumbnail', '') or f"/static/images/{slug}.jpg")

            insights.append({
                "id":           item_id,
                "slug":         slug,
                "lang":         str(post.get('lang', 'en')),
                "title":        str(post.get('title', 'Untitled')),
                "summary":      summary,
                "categories":   cats,
                "intervention": str(post.get('intervention', '')),
                "outcome":      str(post.get('outcome', '')),
                "effect_label": _format_effect(post),
                "effect_min":   post.get('effect_min'),
                "effect_max":   post.get('effect_max'),
                "effect_unit":  str(post.get('effect_unit', 'percent_relative')),
                "effect_direction": str(post.get('effect_direction', 'increase')),
                "sample_context": str(post.get('sample_context', '')),
                "confidence":   str(post.get('confidence', 'estimate')),
                "hook":         str(post.get('hook', '') or post.get('summary', '')),
                "thumbnail":    thumbnail,
                "published":    _normalize_published(post.get('date', ''), fpath),
                "link":         f"/insight/{item_id}",
            })
        except Exception as e:
            print(f"❌ Skip {filename}: {e}")

    insights.sort(key=lambda x: (x['published'], x['id']), reverse=True)

    output = {
        "last_updated": datetime.now().strftime("%Y.%m.%d"),
        "total_count":  len(insights),
        data_key:       insights,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"🎉 Done: {len(insights)} insights -> insights_data.json")


if __name__ == "__main__":
    main()
