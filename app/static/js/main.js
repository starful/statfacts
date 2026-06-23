/**
 * StatFacts — search + category filter + insight cards (no map)
 */

import { CATEGORY_MAP, CATEGORY_ORDER, CONFIDENCE_CLASS, HOME_CATEGORY_LIMIT } from './config.js';

function getHomeLimit() {
    const root = document.getElementById('insights-root');
    const n = parseInt(root?.dataset?.homeLimit || '', 10);
    return Number.isFinite(n) && n > 0 ? n : HOME_CATEGORY_LIMIT;
}

let allInsights = [];
let currentTheme = 'all';
let searchQuery = '';

async function loadInsights() {
    const res = await fetch('/api/insights');
    const data = await res.json();
    const key = Object.keys(data).find(k => Array.isArray(data[k]));
    allInsights = data[key] || [];

    const el = document.getElementById('last-updated-date');
    if (el) el.textContent = data.last_updated || '';
}

function itemMatchesTheme(item, themeKey) {
    const mapped = CATEGORY_MAP[themeKey];
    return (item.categories || []).some(c =>
        c.toLowerCase() === themeKey || c === mapped
    );
}

function sortByPublishedDesc(items) {
    return items.slice().sort((a, b) => {
        const da = String(a.published || '').slice(0, 10);
        const db = String(b.published || '').slice(0, 10);
        if (da !== db) return db.localeCompare(da);
        return String(a.id || '').localeCompare(String(b.id || ''));
    });
}

function getFilteredData() {
    const q = searchQuery.trim().toLowerCase();
    const searchActive = Boolean(q);

    return allInsights.filter(item => {
        if (!searchActive && currentTheme !== 'all') {
            if (!itemMatchesTheme(item, currentTheme)) return false;
        }
        if (!q) return true;

        const haystack = [
            item.title,
            item.summary,
            item.hook,
            item.intervention,
            item.outcome,
            item.effect_label,
            item.sample_context,
            ...(item.categories || []),
        ].filter(Boolean).join(' ').toLowerCase();

        return haystack.includes(q);
    });
    return sortByPublishedDesc(filtered);
}

function setSearchMode(active) {
    document.body.classList.toggle('is-searching', active);
    document.querySelectorAll('.featured-categories-section, .guide-highlight-section').forEach(el => {
        el.hidden = active;
    });
}

function confidenceBadge(confidence) {
    const cls = CONFIDENCE_CLASS[confidence] || 'badge-estimate';
    const label = (confidence || 'estimate').replace(/_/g, ' ');
    return `<span class="confidence-badge ${cls}">${label}</span>`;
}

function renderCard(item) {
    const visual = item.thumbnail
        ? `<div class="card-visual">
                <img src="${item.thumbnail}" alt="" class="card-thumb" loading="lazy">
                <span class="effect-overlay">${item.effect_label || '—'}</span>
           </div>`
        : `<div class="effect-block">${item.effect_label || '—'}</div>`;
    return `
    <article class="insight-card">
        <a href="${item.link}" class="insight-card-link">
            ${visual}
            <div class="card-content">
                <h3 class="card-title">${item.title}</h3>
                <p class="card-preview">${item.hook || item.summary}</p>
                <div class="card-meta">
                    ${confidenceBadge(item.confidence)}
                    <span class="meta-context">${item.sample_context ? item.sample_context.slice(0, 60) + (item.sample_context.length > 60 ? '…' : '') : ''}</span>
                </div>
                <div class="card-tags">
                    ${(item.categories || []).slice(0, 3).map(c => `<span class="tag">${c}</span>`).join('')}
                </div>
            </div>
        </a>
    </article>`;
}

function renderInsights(data) {
    const container = document.getElementById('insights-root');
    if (!container) return;

    const isSearch = Boolean(searchQuery.trim());
    const isSingleCategory = currentTheme !== 'all';

    if (isSearch || isSingleCategory) {
        const title = isSearch
            ? 'Search results'
            : (CATEGORY_MAP[currentTheme] || 'Insights');
        if (data.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No insights match your filters.</p>
                </div>`;
            return;
        }
        container.innerHTML = `
            <section class="category-section" id="category-${currentTheme}">
                <h2 class="section-title">${title}</h2>
                <div class="insight-grid">${data.map(renderCard).join('')}</div>
            </section>`;
        return;
    }

    const homeLimit = getHomeLimit();
    const sections = CATEGORY_ORDER
        .map(key => {
            const all = sortByPublishedDesc(data.filter(item => itemMatchesTheme(item, key)));
            return {
                key,
                label: CATEGORY_MAP[key],
                items: all.slice(0, homeLimit),
                total: all.length,
            };
        })
        .filter(section => section.items.length > 0);

    if (sections.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No insights yet.</p>
            </div>`;
        return;
    }

    container.innerHTML = sections.map(section => `
        <section class="category-section" id="category-${section.key}">
            <h2 class="section-title">
                <a href="/category/${section.key}" class="section-title-link">${section.label}</a>
            </h2>
            <div class="insight-grid">
                ${section.items.map(renderCard).join('')}
            </div>
            ${section.total > homeLimit ? `
            <div class="section-view-all">
                <a href="/category/${section.key}">View all ${section.total} →</a>
            </div>` : ''}
        </section>
    `).join('');
}

function updateCounts() {
    const totalEl = document.getElementById('total-items');
    const allEl   = document.getElementById('count-all');
    if (totalEl) totalEl.textContent = allInsights.length;
    if (allEl)   allEl.textContent   = allInsights.length;

    for (const [key] of Object.entries(CATEGORY_MAP)) {
        const badge = document.getElementById(`count-${key}`);
        if (!badge) continue;
        const cnt = allInsights.filter(i => itemMatchesTheme(i, key)).length;
        badge.textContent = cnt;
    }
}

function updateUI({ scrollToCategory = false } = {}) {
    const isSearch = Boolean(searchQuery.trim());
    setSearchMode(isSearch);
    renderInsights(getFilteredData());
    updateCounts();

    if (isSearch) {
        const listSection = document.getElementById('list-section');
        if (listSection) listSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
    }

    if (scrollToCategory && currentTheme !== 'all') {
        const sec = document.getElementById(`category-${currentTheme}`);
        if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

async function initApp() {
    try {
        await loadInsights();
        updateUI();
    } catch (err) {
        console.error('StatFacts: initial load failed', err);
    }
}

document.querySelectorAll('.theme-button').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.theme-button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTheme = btn.dataset.theme;
        updateUI({ scrollToCategory: currentTheme !== 'all' });
    });
});

const searchInput = document.getElementById('insight-search');
if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value;
        updateUI();
    });
}

initApp();
