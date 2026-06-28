import os

# ============================================================
#  StatFacts — curated effect-size insights (English MVP)
# ============================================================

SITE_CONFIG = {

    # ----------------------------------------------------------
    # 1. Basic identity
    # ----------------------------------------------------------
    "project_name":  "statfacts",
    "site_name":     "StatFacts",
    "site_url":      os.getenv("SITE_URL", "http://localhost:8080"),
    "tagline":       "Benchmarks with context and sources.",
    "meta_description": "Curated effect sizes with ranges, sources, and real-world context — UX, business, sports, and more.",
    "data_key":      "insights",
    "homepage_category_limit": 6,
    "homepage_latest_limit": 6,

    # ----------------------------------------------------------
    # 2. SEO / analytics
    # ----------------------------------------------------------
    "ga_id":         os.getenv("GA_ID", "G-PRF80TCG3Z"),
    "asset_version": os.getenv("ASSET_VERSION", "2026-06-28a"),

    # ----------------------------------------------------------
    # 3. Icon & theme
    # ----------------------------------------------------------
    "emoji":         "📊",
    "logo_url":      "/static/images/logo.png?v=4",
    "logo_icon_url": "/static/images/logo-icon.png?v=2",
    "accent_color":  "#2563eb",
    "bg_dot_color":  "#93c5fd",

    # ----------------------------------------------------------
    # 4. Featured categories (homepage + SEO landing pages)
    # ----------------------------------------------------------
    "featured_categories": [
        {
            "theme": "ux",
            "label": "UX & Web",
            "emoji": "🖥️",
            "description": "Signup flows, checkout fields, and page speed—sourced benchmarks for product teams.",
            "meta_description": "UX and web benchmarks with effect sizes, sources, and context. Signup, checkout, and performance insights.",
        },
        {
            "theme": "business",
            "label": "Business",
            "emoji": "📈",
            "description": "Conversion, growth, and operations stats tied to real decisions and cited studies.",
            "meta_description": "Business benchmarks and effect sizes for conversion, growth, and productivity—with sources.",
        },
        {
            "theme": "sports",
            "label": "Sports",
            "emoji": "⚾",
            "description": "Performance splits and technique trade-offs from published sports data.",
            "meta_description": "Sports statistics and benchmark insights—technique, performance, and cited research.",
        },
        {
            "theme": "health",
            "label": "Health",
            "emoji": "💤",
            "description": "Sleep, habits, and wellness effects with study-backed ranges.",
            "meta_description": "Health and wellness benchmarks with effect sizes, study context, and sources.",
        },
        {
            "theme": "gaming",
            "label": "Gaming",
            "emoji": "🎮",
            "description": "Retention, monetization, and UX levers for games—when data exists.",
            "meta_description": "Gaming benchmarks: retention, monetization, and player experience insights with sources.",
        },
        {
            "theme": "food",
            "label": "Food",
            "emoji": "🍽️",
            "description": "Kitchen, dining, and nutrition stats worth knowing before you change a recipe.",
            "meta_description": "Food and nutrition benchmarks with cited sources and practical effect sizes.",
        },
        {
            "theme": "hr",
            "label": "HR",
            "emoji": "👥",
            "description": "Hiring, retention, and workplace policy effects from published research.",
            "meta_description": "HR and workplace benchmarks—hiring, retention, and policy insights with sources.",
        },
        {
            "theme": "travel",
            "label": "Travel",
            "emoji": "✈️",
            "description": "Booking, pricing, and trip-planning numbers that change traveler behavior.",
            "meta_description": "Travel benchmarks and statistics with sources—booking, pricing, and planning insights.",
        },
    ],

    # ----------------------------------------------------------
    # 5. Header filter buttons
    # ----------------------------------------------------------
    "filter_buttons": [
        {"label": "All",        "theme": "all",       "count_id": "count-all"},
        {"label": "UX & Web",   "theme": "ux",        "count_id": "count-ux"},
        {"label": "Business",   "theme": "business",  "count_id": "count-business"},
        {"label": "Gaming",     "theme": "gaming",    "count_id": "count-gaming"},
        {"label": "Food",       "theme": "food",      "count_id": "count-food"},
        {"label": "HR",         "theme": "hr",          "count_id": "count-hr"},
        {"label": "Travel",     "theme": "travel",    "count_id": "count-travel"},
        {"label": "Sports",     "theme": "sports",    "count_id": "count-sports"},
        {"label": "Health",     "theme": "health",    "count_id": "count-health"},
    ],

    # ----------------------------------------------------------
    # 6. Category mapping (source -> UI label)
    # ----------------------------------------------------------
    "category_mapping": {
        "ux": "UX & Web",
        "business": "Business",
        "gaming": "Gaming",
        "food": "Food",
        "hr": "HR",
        "travel": "Travel",
        "sports": "Sports",
        "health": "Health",
        "saas": "SaaS",
        "signup": "Signup",
        "checkout": "Checkout",
        "baseball": "Baseball",
    },

    # ----------------------------------------------------------
    # 7. JS category map
    # ----------------------------------------------------------
    "js_category_map": {
        "ux": "UX & Web",
        "business": "Business",
        "gaming": "Gaming",
        "food": "Food",
        "hr": "HR",
        "travel": "Travel",
        "sports": "Sports",
        "health": "Health",
    },

    # ----------------------------------------------------------
    # 8. Detail page schema type (JSON-LD)
    # ----------------------------------------------------------
    "schema_type": "Article",

    # ----------------------------------------------------------
    # 9. Guide section images
    # ----------------------------------------------------------
    "guide_images": [
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?q=80&w=800&auto=format&fit=crop",
    ],
    "guide_image_map": {
        "how-to-read-benchmarks":          "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=800&auto=format&fit=crop",
        "relative-vs-absolute-effects":    "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=800&auto=format&fit=crop",
        "confidence-levels-explained":     "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?q=80&w=800&auto=format&fit=crop",
        "when-not-to-use-a-benchmark":     "https://images.unsplash.com/photo-1573164574432-00b9b5a2f2c6?q=80&w=800&auto=format&fit=crop",
        "how-to-cite-in-a-deck":           "https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=800&auto=format&fit=crop",
        "planning-ab-test-from-benchmark": "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?q=80&w=800&auto=format&fit=crop",
    },

    # ----------------------------------------------------------
    # 10. Footer
    # ----------------------------------------------------------
    "footer_tagline":  "Curated benchmarks with context, ranges, and sources.",
    "footer_year":     "2026",
}
