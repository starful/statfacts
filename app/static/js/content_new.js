/** Homepage NEW badge — keep in sync with app/content_new.py (NEW_CONTENT_DAYS). */
export const NEW_CONTENT_DAYS = 14;

export function isContentNew(published) {
    if (!published) return false;
    const d = new Date(String(published).slice(0, 10) + 'T00:00:00');
    if (Number.isNaN(d.getTime())) return false;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - NEW_CONTENT_DAYS);
    cutoff.setHours(0, 0, 0, 0);
    return d >= cutoff;
}

export function newBadgeHtml(isNew, label = 'New') {
    if (!isNew) return '';
    return `<span class="badge-new">${label}</span>`;
}

export function formatPublished(published) {
    return published ? String(published).slice(0, 10) : '';
}
