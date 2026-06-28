from flask import Flask, jsonify, render_template, abort, redirect, request, Response, send_from_directory
from flask_compress import Compress
import json, os, frontmatter, markdown, re, glob, hashlib, copy, urllib.request, io
from datetime import datetime, date, timedelta
from urllib.parse import quote

app = Flask(__name__)
Compress(app)

try:
    from .reactions import reactions_bp
except ImportError:
    from reactions import reactions_bp

app.register_blueprint(reactions_bp)

try:
    from .config import SITE_CONFIG
    from .card_renderer import render_insight_card, OG_SIZE, LIST_SIZE
except ImportError:
    from config import SITE_CONFIG
    from card_renderer import render_insight_card, OG_SIZE, LIST_SIZE

try:
    from .content_new import enrich_items, enrich_item
except ImportError:
    from content_new import enrich_items, enrich_item

BASE_DIR    = app.root_path
STATIC_DIR  = os.path.join(BASE_DIR, 'static')
DATA_FILE   = os.path.join(STATIC_DIR, 'json', 'insights_data.json')
CONTENT_DIR = os.path.join(BASE_DIR, 'content')
GUIDE_DIR   = os.path.join(CONTENT_DIR, 'guides')

GUIDE_IMAGES = SITE_CONFIG['guide_images']
GUIDE_IMAGE_MAP = SITE_CONFIG.get('guide_image_map', {})
DATA_KEY = SITE_CONFIG['data_key']
CONFIDENCE_LABELS = {
    'meta_analysis': 'Meta-analysis',
    'ab_test': 'A/B test',
    'study': 'Study',
    'estimate': 'Estimate',
}


def get_mapped_image(base_id, override=None):
    if override:
        return override
    if base_id in GUIDE_IMAGE_MAP:
        return GUIDE_IMAGE_MAP[base_id]
    idx = int(hashlib.md5(base_id.encode()).hexdigest(), 16) % len(GUIDE_IMAGES)
    return GUIDE_IMAGES[idx]


def _thumbnail_cache_v(published_or_date: str | None) -> str:
    v = str(published_or_date or "").strip()[:10]
    return v if len(v) >= 8 else ""


def _thumbnail_with_v(url: str, cache_v: str | None = None) -> str:
    if not url:
        return url
    v = _thumbnail_cache_v(cache_v)
    base = url.split("?", 1)[0]
    return f"{base}?v={v}" if v else base


def _public_insight(item: dict) -> dict:
    out = copy.deepcopy(item)
    out["thumbnail"] = _thumbnail_with_v(out.get("thumbnail", ""), out.get("published"))
    return out


CACHED_DATA   = {DATA_KEY: [], "last_updated": ""}
CACHED_GUIDES = {'en': []}
_CACHE_MTIME: float = 0.0


def load_insights():
    global CACHED_DATA, _CACHE_MTIME
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                CACHED_DATA = json.load(f)
            _CACHE_MTIME = os.path.getmtime(DATA_FILE)
            print(f"✅ Data loaded: {len(CACHED_DATA.get(DATA_KEY, []))} insights")
        except Exception as e:
            print(f"❌ Data load error: {e}")


def _ensure_insights_cache() -> None:
    global CACHED_DATA, _CACHE_MTIME
    if not os.path.exists(DATA_FILE):
        return
    try:
        mtime = os.path.getmtime(DATA_FILE)
    except OSError:
        return
    if mtime <= _CACHE_MTIME:
        return
    load_insights()


def load_guides():
    global CACHED_GUIDES
    if not os.path.exists(GUIDE_DIR):
        return

    all_raw = []
    for fpath in glob.glob(os.path.join(GUIDE_DIR, '*.md')):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                raw = f.read().strip()
            raw = _clean_md(raw)
            post = frontmatter.loads(raw)
            if str(post.get('lang', 'en')) != 'en':
                continue
            base_id = os.path.basename(fpath).replace('.md', '')
            all_raw.append({
                'base_id': base_id,
                'full_id': base_id,
                'title':   str(post.get('title', 'Guide')),
                'summary': str(post.get('summary', '')),
                'date':    str(post.get('date', '2026-01-01')),
                'image':   str(post.get('image', '') or ''),
            })
        except Exception:
            continue

    guides = []
    for g in sorted(all_raw, key=lambda x: x['date'], reverse=True):
        guides.append({
            'id':        g['full_id'],
            'title':     g['title'],
            'summary':   g['summary'],
            'thumbnail': get_mapped_image(g['base_id'], g.get('image') or None),
            'published': g['date'],
        })

    CACHED_GUIDES = {'en': guides}
    print(f"✅ Guides loaded: {len(guides)}")


def _clean_md(text):
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    text = re.sub(r'^(##\s*)?yaml\n', '', text, flags=re.IGNORECASE)
    if '---' in text and not text.startswith('---'):
        text = '---' + text.split('---', 1)[1]
    return text.strip()


def _get_footer_stats():
    items = CACHED_DATA.get(DATA_KEY, [])
    return {
        'total_items':  len(items),
        'last_updated': CACHED_DATA.get('last_updated', ''),
        'site':         SITE_CONFIG,
    }


def _insight_matches_theme(item, theme_key, mapping):
    mapped = mapping.get(theme_key, theme_key)
    cats = [str(c).strip() for c in item.get('categories', [])]
    return any(c.lower() == theme_key or c == mapped for c in cats)


def _normalize_sitemap_date(raw: str | None, *, fallback: str | None = None) -> str:
    """Normalize published / last_updated to YYYY-MM-DD for sitemap lastmod."""
    if not raw:
        return fallback or date.today().isoformat()
    s = str(raw).strip()
    if re.match(r'^\d{4}\.\d{2}\.\d{2}', s):
        y, m, d = s[:10].split('.')
        return f"{y}-{m}-{d}"
    s = s[:10]
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        return fallback or date.today().isoformat()


def _file_lastmod(path: str) -> str:
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d')
    except OSError:
        return date.today().isoformat()


def _max_published(items: list[dict], *, key: str = 'published') -> str | None:
    dates = [_normalize_sitemap_date(i.get(key)) for i in items if i.get(key)]
    return max(dates) if dates else None


def _sitemap_url(loc: str, lastmod: str, changefreq: str) -> str:
    return (
        f"<url><loc>{loc}</loc>"
        f"<lastmod>{lastmod}</lastmod>"
        f"<changefreq>{changefreq}</changefreq></url>"
    )


def _category_sections(items, limit=None):
    mapping = SITE_CONFIG.get('js_category_map', {})
    if limit is None:
        limit = int(SITE_CONFIG.get('homepage_category_limit', 6))
    sections = []
    for btn in SITE_CONFIG.get('filter_buttons', []):
        key = btn.get('theme')
        if not key or key == 'all':
            continue
        matched = [i for i in items if _insight_matches_theme(i, key, mapping)]
        matched.sort(key=lambda x: (x.get('published', ''), x.get('id', '')), reverse=True)
        if matched:
            sections.append({
                'theme': key,
                'label': btn.get('label', key),
                'insights': enrich_items([_public_insight(i) for i in matched[:limit]]),
                'total': len(matched),
            })
    return sections


def _latest_insights(items, limit=None):
    if limit is None:
        limit = int(SITE_CONFIG.get('homepage_latest_limit', 6))
    return enrich_items([_public_insight(i) for i in items[:limit]])


def _featured_category_lookup():
    return {c['theme']: c for c in SITE_CONFIG.get('featured_categories', [])}


def _featured_categories(items):
    mapping = SITE_CONFIG.get('js_category_map', {})
    featured = []
    for cat in SITE_CONFIG.get('featured_categories', []):
        theme = cat['theme']
        count = sum(1 for i in items if _insight_matches_theme(i, theme, mapping))
        featured.append({**cat, 'count': count})
    return featured


def _category_by_theme(theme):
    cat = _featured_category_lookup().get(theme)
    if not cat:
        return None
    mapping = SITE_CONFIG.get('js_category_map', {})
    label = mapping.get(theme, cat.get('label', theme))
    return {**cat, 'label': label}


def _primary_category_for_item(categories):
    mapping = SITE_CONFIG.get('js_category_map', {})
    cat_set = {str(c).strip() for c in (categories or [])}
    for featured in SITE_CONFIG.get('featured_categories', []):
        theme = featured.get('theme')
        if not theme:
            continue
        mapped = mapping.get(theme, featured.get('label', theme))
        if theme in cat_set or mapped in cat_set:
            return theme, mapped
    return None, None


def _absolute_url(path_or_url):
    if not path_or_url:
        return ""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    return f"{SITE_CONFIG['site_url'].rstrip('/')}/{path_or_url.lstrip('/')}"


def _gcs_image_url(filename: str) -> str:
    """Direct public GCS URL — reliable for OG/Twitter crawlers (no redirect)."""
    project = SITE_CONFIG["project_name"]
    return f"https://storage.googleapis.com/ok-project-assets/{project}/{filename}"


def _social_image_url(slug: str) -> str:
    """Same-domain OG image URL (proxies GCS) for social crawlers."""
    return f"{SITE_CONFIG['site_url'].rstrip('/')}/social/{slug}.jpg"


def _linkedin_inspector_url(page_url: str) -> str:
    return f"https://www.linkedin.com/post-inspector/inspect/{quote(page_url, safe='')}"


def _related_insights(current_id, categories, limit=3):
    items = CACHED_DATA.get(DATA_KEY, [])
    related = []
    cat_set = set(categories or [])
    for item in items:
        if item.get('id') == current_id:
            continue
        if cat_set & set(item.get('categories', [])):
            related.append(item)
    if len(related) < limit:
        for item in items:
            if item.get('id') == current_id:
                continue
            if item not in related:
                related.append(item)
            if len(related) >= limit:
                break
    return [_public_insight(i) for i in related[:limit]]


def _insight_for_card(insight_id: str) -> dict | None:
    for item in CACHED_DATA.get(DATA_KEY, []):
        if item.get('id') == insight_id:
            return item
    md_path = os.path.join(CONTENT_DIR, f"{insight_id}.md")
    if not os.path.exists(md_path):
        return None
    with open(md_path, 'r', encoding='utf-8') as f:
        post = frontmatter.loads(_clean_md(f.read()))
    cats = post.get('categories', [])
    if isinstance(cats, str):
        cats = [c.strip() for c in cats.split(',')]
    lo, hi = post.get('effect_min'), post.get('effect_max')
    sign = '+' if str(post.get('effect_direction', 'increase')) != 'decrease' else '-'
    if lo is not None and hi is not None and lo != hi:
        effect_label = f"{sign}{lo}–{hi}%"
    elif lo is not None or hi is not None:
        val = hi if hi is not None else lo
        effect_label = f"{sign}{val}%"
    else:
        effect_label = str(post.get('effect_label', '—'))
    return {
        'id': insight_id,
        'title': str(post.get('title', '')),
        'hook': str(post.get('hook', '') or post.get('summary', '')),
        'effect_label': effect_label,
        'categories': cats,
        'summary': str(post.get('summary', '')),
    }


CATEGORY_MAPPING = SITE_CONFIG.get('category_mapping', {})

load_insights()
load_guides()


@app.route('/')
def index():
    _ensure_insights_cache()
    items = CACHED_DATA.get(DATA_KEY, [])
    top_guides = CACHED_GUIDES.get('en', [])[:3]
    stats = _get_footer_stats()
    return render_template(
        'index.html',
        lang='en',
        guides=CACHED_GUIDES,
        top_guides=top_guides,
        latest_insights=_latest_insights(items),
        category_sections=_category_sections(items),
        featured_categories=_featured_categories(items),
        canonical=SITE_CONFIG['site_url'],
        **stats,
    )


@app.route('/category/<theme>')
def category_page(theme):
    _ensure_insights_cache()
    cat = _category_by_theme(theme)
    if not cat:
        abort(404)
    items = CACHED_DATA.get(DATA_KEY, [])
    mapping = SITE_CONFIG.get('js_category_map', {})
    insights = enrich_items([_public_insight(i) for i in items if _insight_matches_theme(i, theme, mapping)])
    insights.sort(key=lambda x: (x.get('published', ''), x.get('id', '')), reverse=True)
    stats = _get_footer_stats()
    canonical = f"{SITE_CONFIG['site_url'].rstrip('/')}/category/{theme}"
    return render_template(
        'category.html',
        category=cat,
        insights=insights,
        canonical=canonical,
        **stats,
    )


@app.route('/api/insights')
def api_insights():
    _ensure_insights_cache()
    items = CACHED_DATA.get(DATA_KEY, [])
    spoofed = []
    for item in items:
        s = _public_insight(item)
        new_cats = [CATEGORY_MAPPING.get(c.strip(), c.strip()) for c in s.get('categories', [])]
        s['categories'] = list(dict.fromkeys(new_cats))
        s['confidence_label'] = CONFIDENCE_LABELS.get(s.get('confidence', ''), s.get('confidence', ''))
        spoofed.append(s)
    spoofed = enrich_items(spoofed)
    return jsonify({DATA_KEY: spoofed, "last_updated": CACHED_DATA.get('last_updated')})


@app.route('/social/<slug>.jpg')
def social_image(slug):
    """Serve Imagen thumbnail on-site for OG/Twitter/LinkedIn (1200×630, no redirect)."""
    safe = re.sub(r"[^a-z0-9-]", "", slug.lower())
    if not safe:
        abort(404)
    gcs_url = _gcs_image_url(f"{safe}.jpg")
    try:
        with urllib.request.urlopen(gcs_url, timeout=15) as resp:
            raw = resp.read()
            if not raw:
                abort(404)
    except Exception:
        abort(404)

    try:
        from PIL import Image, ImageOps

        img = Image.open(io.BytesIO(raw)).convert("RGB")
        data = _jpeg_bytes(ImageOps.fit(img, (1200, 630), Image.Resampling.LANCZOS))
    except Exception:
        data = raw

    return Response(
        data,
        mimetype="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


def _jpeg_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88, optimize=True)
    return buf.getvalue()


@app.route('/og/insight/<insight_id>.png')
def og_insight_card(insight_id):
    """Option B: programmatic PNG card (OG or list size)."""
    item = _insight_for_card(insight_id)
    if not item:
        abort(404)
    size = LIST_SIZE if request.args.get('size') == 'list' else OG_SIZE
    category = ''
    if item.get('categories'):
        category = CATEGORY_MAPPING.get(item['categories'][0], item['categories'][0])
    png = render_insight_card(
        effect_label=item.get('effect_label', '—'),
        hook=item.get('hook') or item.get('summary', ''),
        title=item.get('title', ''),
        category=category,
        site_name=SITE_CONFIG['site_name'],
        size=size,
    )
    return Response(png, mimetype='image/png')


@app.route('/demo/cards')
def demo_cards():
    """Preview page for Option B programmatic cards."""
    samples = []
    for item in CACHED_DATA.get(DATA_KEY, []):
        enriched = copy.deepcopy(item)
        if not enriched.get('hook'):
            md_path = os.path.join(CONTENT_DIR, f"{enriched['id']}.md")
            if os.path.exists(md_path):
                with open(md_path, 'r', encoding='utf-8') as f:
                    post = frontmatter.loads(_clean_md(f.read()))
                enriched['hook'] = str(post.get('hook', '') or post.get('summary', ''))
        samples.append(enriched)
    return render_template('demo_cards.html', samples=samples, **_get_footer_stats())


def _benchmark_calculator_url(post: dict) -> str | None:
    """Build deep-link query for /tools/benchmark-calculator from insight frontmatter."""
    lo, hi = post.get('effect_min'), post.get('effect_max')
    if lo is None and hi is None:
        return None
    from urllib.parse import urlencode

    params = {
        'from': str(post.get('id', '')),
        'title': str(post.get('title', '')),
        'min': lo if lo is not None else hi,
        'max': hi if hi is not None else lo,
        'unit': str(post.get('effect_unit', 'percent_relative')),
        'direction': str(post.get('effect_direction', 'increase')),
    }
    return '/tools/benchmark-calculator?' + urlencode(params)


@app.route('/tools/benchmark-calculator')
def benchmark_calculator():
    stats = _get_footer_stats()
    return render_template(
        'tools/benchmark_calculator.html',
        canonical=f"{SITE_CONFIG['site_url'].rstrip('/')}/tools/benchmark-calculator",
        **stats,
    )


@app.route('/guide')
def guide_list():
    stats = _get_footer_stats()
    return render_template(
        'guide_list.html',
        guides=CACHED_GUIDES,
        lang='en',
        canonical=f"{SITE_CONFIG['site_url']}/guide",
        **stats,
    )


@app.route('/guide/<guide_id>')
def guide_detail(guide_id):
    path = os.path.join(GUIDE_DIR, f"{guide_id}.md")
    if not os.path.exists(path):
        return redirect('/guide')

    with open(path, 'r', encoding='utf-8') as f:
        raw = _clean_md(f.read())
    post = frontmatter.loads(raw)
    body = re.sub(r'---.*?---', '', post.content, flags=re.DOTALL)
    body = body.replace('```markdown', '').replace('```', '').strip()

    title = str(post.get('title') or guide_id)
    image = get_mapped_image(guide_id, str(post.get('image', '') or '') or None)
    stats = _get_footer_stats()
    content_html = markdown.markdown(body, extensions=['tables', 'toc', 'fenced_code'])
    return render_template(
        'guide_detail.html',
        title=title,
        content=content_html,
        lang='en',
        guide_id=guide_id,
        base_id=guide_id,
        image_url=image,
        image_url_abs=_absolute_url(image),
        canonical=f"{SITE_CONFIG['site_url']}/guide/{guide_id}",
        alt_en=f"{SITE_CONFIG['site_url']}/guide/{guide_id}",
        alt_ko=f"{SITE_CONFIG['site_url']}/guide/{guide_id}",
        post=post,
        **stats,
    )


@app.route('/insight/<insight_id>')
def insight_detail(insight_id):
    md_path = os.path.join(CONTENT_DIR, f"{insight_id}.md")
    if not os.path.exists(md_path):
        abort(404)

    with open(md_path, 'r', encoding='utf-8') as f:
        raw = _clean_md(f.read())
    post = frontmatter.loads(raw)

    if isinstance(post.get('categories'), str):
        post['categories'] = [c.strip() for c in post.get('categories').split(',')]

    sources = post.get('sources', [])
    if isinstance(sources, dict):
        sources = [sources]

    post['id'] = insight_id
    post['confidence_label'] = CONFIDENCE_LABELS.get(
        str(post.get('confidence', '')), str(post.get('confidence', 'estimate'))
    )

    content_html = markdown.markdown(post.content, extensions=['tables', 'fenced_code'])
    stats = _get_footer_stats()
    related = _related_insights(insight_id, post.get('categories', []))

    effect_parts = []
    if post.get('effect_min') is not None or post.get('effect_max') is not None:
        lo = post.get('effect_min')
        hi = post.get('effect_max')
        sign = '+' if str(post.get('effect_direction', 'increase')) != 'decrease' else '-'
        if lo is not None and hi is not None and lo != hi:
            effect_parts.append(f"{sign}{lo}–{hi}%")
        else:
            val = hi if hi is not None else lo
            effect_parts.append(f"{sign}{val}%")
    post['effect_display'] = effect_parts[0] if effect_parts else str(post.get('effect_label', ''))
    post['hook'] = str(post.get('hook', '') or post.get('summary', ''))

    slug = str(post.get('id', insight_id)).replace('_en', '').replace('_ko', '')
    post['thumbnail'] = _thumbnail_with_v(
        str(post.get('thumbnail', '') or f"/static/images/{slug}.jpg"),
        _thumbnail_cache_v(post.get("date") or post.get("published")),
    )

    primary_theme, primary_label = _primary_category_for_item(post.get('categories', []))

    share_url = f"{SITE_CONFIG['site_url'].rstrip('/')}/insight/{insight_id}"
    share_text = f"{post['hook']} → {post['effect_display']}"
    og_image_abs = _social_image_url(slug)

    calculator_url = _benchmark_calculator_url(post)

    return render_template(
        'detail.html',
        post=post,
        content=content_html,
        sources=sources,
        related=related,
        primary_category_theme=primary_theme,
        primary_category_label=primary_label,
        thumbnail_abs=_absolute_url(post['thumbnail']) if post.get('thumbnail') else '',
        og_image_abs=og_image_abs,
        og_image_width=1200,
        og_image_height=630,
        share_id=insight_id,
        share_url=share_url,
        share_text=share_text,
        share_tweet=share_text,
        linkedin_inspector_url=_linkedin_inspector_url(share_url),
        calculator_url=calculator_url,
        **stats,
    )


@app.route('/item/<item_id>')
def legacy_item_redirect(item_id):
    return redirect(f'/insight/{item_id}', code=301)


@app.route('/api/items')
def legacy_api_items():
    return redirect('/api/insights', code=301)


@app.route('/static/images/<path:filename>')
def serve_images(filename):
    """Serve local images when present; otherwise redirect to GCS (production)."""
    image_dir = os.path.join(STATIC_DIR, 'images')
    local_path = os.path.join(image_dir, filename)
    if os.path.isfile(local_path):
        return send_from_directory(image_dir, filename)
    project_name = SITE_CONFIG['project_name']
    url = f"https://storage.googleapis.com/ok-project-assets/{project_name}/{filename}"
    if request.query_string:
        url = f"{url}?{request.query_string.decode()}"
    return redirect(url, code=302)


@app.route('/favicon.ico')
@app.route('/favicon-32x32.png')
@app.route('/apple-touch-icon.png')
@app.route('/android-chrome-192x192.png')
def serve_favicons():
    image_dir = os.path.join(STATIC_DIR, 'images')
    filename = request.path[1:]
    local_path = os.path.join(image_dir, filename)
    if os.path.exists(local_path):
        mimetype = 'image/png' if filename.endswith('.png') else 'image/vnd.microsoft.icon'
        return send_from_directory(image_dir, filename, mimetype=mimetype)
    return Response(status=404)


@app.route('/site.webmanifest')
def webmanifest():
    manifest_path = os.path.join(STATIC_DIR, 'site.webmanifest')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='application/manifest+json')
    return Response('{"name":"StatFacts","icons":[]}', mimetype='application/manifest+json')


@app.route('/robots.txt')
def robots_txt():
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        f"Sitemap: {SITE_CONFIG['site_url'].rstrip('/')}/sitemap.xml\n"
    )
    return Response(content, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    _ensure_insights_cache()
    base = SITE_CONFIG['site_url'].rstrip('/')
    items = CACHED_DATA.get(DATA_KEY, [])
    mapping = SITE_CONFIG.get('js_category_map', {})
    guides = CACHED_GUIDES.get('en', [])

    insight_dates = [_normalize_sitemap_date(i.get('published')) for i in items if i.get('published')]
    home_lastmod = (
        max(insight_dates)
        if insight_dates
        else _normalize_sitemap_date(CACHED_DATA.get('last_updated'))
    )
    guide_lastmod = _max_published(guides) or home_lastmod

    templates_dir = os.path.join(BASE_DIR, 'templates')
    about_lastmod = _file_lastmod(os.path.join(templates_dir, 'about.html'))
    privacy_lastmod = _file_lastmod(os.path.join(templates_dir, 'privacy.html'))

    tool_lastmod = _file_lastmod(os.path.join(templates_dir, 'tools', 'benchmark_calculator.html'))

    nodes: list[str] = [
        _sitemap_url(f"{base}/", home_lastmod, 'weekly'),
        _sitemap_url(f"{base}/guide", guide_lastmod, 'weekly'),
        _sitemap_url(f"{base}/tools/benchmark-calculator", tool_lastmod, 'monthly'),
        _sitemap_url(f"{base}/about.html", about_lastmod, 'monthly'),
        _sitemap_url(f"{base}/privacy.html", privacy_lastmod, 'monthly'),
    ]

    for cat in SITE_CONFIG.get('featured_categories', []):
        theme = cat.get('theme')
        if not theme:
            continue
        matched = [i for i in items if _insight_matches_theme(i, theme, mapping)]
        cat_lastmod = _max_published(matched) or home_lastmod
        nodes.append(_sitemap_url(f"{base}/category/{theme}", cat_lastmod, 'weekly'))

    for item in items:
        link = item.get('link', '')
        if not link:
            continue
        pub = _normalize_sitemap_date(item.get('published'), fallback=home_lastmod)
        nodes.append(_sitemap_url(f"{base}{link}", pub, 'monthly'))

    for guide in guides:
        gid = guide.get('id')
        if not gid:
            continue
        pub = _normalize_sitemap_date(guide.get('published'), fallback=guide_lastmod)
        nodes.append(_sitemap_url(f"{base}/guide/{gid}", pub, 'monthly'))

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + ''.join(nodes) +
        '</urlset>'
    )
    return Response(xml, mimetype='application/xml')


@app.route('/about.html')
def about():
    return render_template('about.html', **_get_footer_stats())


@app.route('/privacy.html')
def privacy():
    return render_template('privacy.html', site=SITE_CONFIG)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
