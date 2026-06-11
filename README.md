# StatFacts

**https://statfacts.net** — Curated **if X → then Y%** benchmarks with context, ranges, and sources.

Built on the OK Series stack: **Markdown → JSON → Flask → Cloud Run**.

## Quick Start (local)

```bash
cd okstats
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python script/build_data.py
SITE_URL=http://localhost:8080 python run.py
```

Open **http://localhost:8080** (or `PORT=8092 python run.py` if 8080 is busy)

### AI thumbnails (Imagen)

```bash
# .env: GEMINI_API_KEY=...
python script/fetch_images.py   # reads image_prompt from each *_en.md
python script/optimize_images.py  # optional resize
python script/build_data.py
```

Each insight has `hook` + `image_prompt` in frontmatter. Images save to `app/static/images/{id}.jpg`.
Later KO/JA: add `{id}_ko.md` with translated hook and a separate `image_prompt` (visual metaphors can stay similar).

## Project Structure

```text
okstats/                     # repo folder (StatFacts app)
├── app/
│   ├── __init__.py          # Routes, cache, sitemap
│   ├── config.py            # Site config (categories, branding)
│   ├── content/             # Insight markdown (source of truth)
│   │   └── guides/          # Methodology guides
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/main.js       # Search + filter (no map)
│   │   └── json/insights_data.json
│   └── templates/
├── script/
│   ├── build_data.py        # Markdown → JSON
│   └── csv/insights.csv     # Seed list for future AI pipeline
└── run.py
```

## Add an insight

1. Create `app/content/my-insight_en.md` with frontmatter (`intervention`, `outcome`, `effect_min`, `effect_max`, `confidence`, `sources`).
2. Run `python script/build_data.py`
3. Restart the server (or redeploy)

## Routes

| Path | Description |
|------|-------------|
| `/` | Search + category filter + insight cards |
| `/insight/{id}` | Detail page |
| `/api/insights` | JSON API |
| `/guide` | Methodology guides |

## English MVP

Launch language is English only. Schema supports future `lang` fields for KO/JA.

**Categories (filters):** UX & Web, Business, Gaming, Food, HR, Travel, Sports, Health. Sub-tags: `saas`, `signup`, `checkout`, `baseball`, etc.

## Production

```bash
SITE_URL=https://statfacts.net ./deploy.sh
```
