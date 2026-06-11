// StatFacts category map — must match js_category_map in app/config.py
export const CATEGORY_MAP = {
    'ux':       'UX & Web',
    'business': 'Business',
    'gaming':   'Gaming',
    'food':     'Food',
    'hr':       'HR',
    'travel':   'Travel',
    'sports':   'Sports',
    'health':   'Health',
};

export const CATEGORY_ORDER = Object.keys(CATEGORY_MAP);

export const HOME_CATEGORY_LIMIT = 6;

export const CONFIDENCE_CLASS = {
    'meta_analysis': 'badge-meta',
    'ab_test':       'badge-ab',
    'study':         'badge-study',
    'estimate':      'badge-estimate',
};
