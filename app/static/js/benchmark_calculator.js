(function () {
    "use strict";

    const Z_ALPHA = { 0.10: 1.645, 0.05: 1.96, 0.01: 2.576 };
    const Z_POWER = { 0.80: 0.84, 0.90: 1.28, 0.95: 1.645 };

    function clampPct(v) {
        return Math.max(0, Math.min(100, v));
    }

    function parseNum(id, fallback) {
        const el = document.getElementById(id);
        if (!el) return fallback;
        const n = parseFloat(el.value);
        return Number.isFinite(n) ? n : fallback;
    }

    function fmtPct(v) {
        return v.toFixed(2) + "%";
    }

    function fmtSigned(v, suffix) {
        const sign = v >= 0 ? "+" : "";
        return sign + v.toFixed(2) + suffix;
    }

    function readQuery() {
        const q = new URLSearchParams(window.location.search);
        return {
            from: q.get("from") || "",
            title: q.get("title") || "",
            min: q.get("min"),
            max: q.get("max"),
            unit: q.get("unit") || "percent_relative",
            direction: q.get("direction") || "increase",
            baseline: q.get("baseline"),
        };
    }

    function applyBenchmark(baselinePct, effectMin, effectMax, unit, direction) {
        let lo = effectMin;
        let hi = effectMax;
        if (lo > hi) {
            const t = lo;
            lo = hi;
            hi = t;
        }

        let newLo;
        let newHi;
        if (unit === "percent_point") {
            if (direction === "decrease") {
                newLo = baselinePct - hi;
                newHi = baselinePct - lo;
            } else {
                newLo = baselinePct + lo;
                newHi = baselinePct + hi;
            }
        } else if (direction === "decrease") {
            newLo = baselinePct * (1 - hi / 100);
            newHi = baselinePct * (1 - lo / 100);
        } else {
            newLo = baselinePct * (1 + lo / 100);
            newHi = baselinePct * (1 + hi / 100);
        }

        newLo = clampPct(newLo);
        newHi = clampPct(newHi);
        if (newLo > newHi) {
            const t = newLo;
            newLo = newHi;
            newHi = t;
        }

        const absLo = newLo - baselinePct;
        const absHi = newHi - baselinePct;
        const midRate = (newLo + newHi) / 2;
        const midLiftRel = baselinePct > 0 ? ((midRate / baselinePct) - 1) * 100 : 0;

        return {
            newLo,
            newHi,
            absLo,
            absHi,
            midRate,
            midLiftRel,
            suggestedMdePp: (absLo + absHi) / 2,
            suggestedMdeRel: (lo + hi) / 2,
        };
    }

    function sampleSizePerVariant(baselinePct, mdeValue, mdeMode, alpha, power, direction) {
        const p1 = baselinePct / 100;
        let delta = mdeMode === "relative_pct"
            ? p1 * (mdeValue / 100)
            : mdeValue / 100;
        delta = direction === "decrease" ? -Math.abs(delta) : Math.abs(delta);

        const p2 = p1 + delta;
        if (!delta || p1 <= 0 || p1 >= 1 || p2 <= 0 || p2 >= 1) {
            return null;
        }

        const pBar = (p1 + p2) / 2;
        const zA = Z_ALPHA[alpha] || 1.96;
        const zB = Z_POWER[power] || 0.84;
        const n = 2 * Math.pow(zA + zB, 2) * pBar * (1 - pBar) / (delta * delta);
        const perVariant = Math.max(1, Math.ceil(n));

        return {
            perVariant,
            total: perVariant * 2,
            deltaPp: delta * 100,
            p2Pct: p2 * 100,
        };
    }

    function showSourceCard(params) {
        const card = document.getElementById("source-card");
        if (!card) return;
        if (!params.from) {
            card.hidden = true;
            return;
        }
        card.hidden = false;
        const titleEl = document.getElementById("source-title");
        const linkEl = document.getElementById("source-link");
        if (titleEl) titleEl.textContent = params.title || params.from;
        if (linkEl) {
            linkEl.href = "/insight/" + encodeURIComponent(params.from);
            linkEl.textContent = "View insight →";
        }
    }

    function updateApplyTab() {
        const baseline = parseNum("apply-baseline", 20);
        const min = parseNum("apply-min", 12);
        const max = parseNum("apply-max", 18);
        const unit = document.getElementById("apply-unit")?.value || "percent_relative";
        const direction = document.getElementById("apply-direction")?.value || "increase";

        const r = applyBenchmark(baseline, min, max, unit, direction);
        const out = document.getElementById("apply-results");
        if (!out) return;

        document.getElementById("result-range").textContent =
            fmtPct(r.newLo) + " – " + fmtPct(r.newHi);
        document.getElementById("result-abs").textContent =
            fmtSigned(r.absLo, " pp") + " – " + fmtSigned(r.absHi, " pp");
        document.getElementById("result-mid").textContent = fmtPct(r.midRate);

        const syncBaseline = document.getElementById("size-baseline");
        if (syncBaseline && document.activeElement?.id !== "size-baseline") {
            syncBaseline.value = String(baseline);
        }

        window.__lastApply = r;
        out.setAttribute("aria-live", "polite");
    }

    function updateSizeTab() {
        const baseline = parseNum("size-baseline", 20);
        const mde = parseNum("size-mde", 1);
        const mdeMode = document.getElementById("size-mde-mode")?.value || "absolute_pp";
        const alpha = parseFloat(document.getElementById("size-alpha")?.value || "0.05");
        const power = parseFloat(document.getElementById("size-power")?.value || "0.80");
        const direction = document.getElementById("size-direction")?.value || "increase";
        const weekly = parseNum("size-weekly", 0);

        const result = sampleSizePerVariant(baseline, mde, mdeMode, alpha, power, direction);
        const out = document.getElementById("size-results");
        const err = document.getElementById("size-error");
        if (!out || !err) return;

        if (!result) {
            out.hidden = true;
            err.hidden = false;
            err.textContent =
                "Check inputs: baseline must be between 0 and 100%, MDE must leave treatment rate inside 0–100%.";
            return;
        }

        err.hidden = true;
        out.hidden = false;
        document.getElementById("size-per-variant").textContent =
            result.perVariant.toLocaleString();
        document.getElementById("size-total").textContent =
            result.total.toLocaleString();
        document.getElementById("size-treatment-rate").textContent = fmtPct(result.p2Pct);

        const durationEl = document.getElementById("size-duration");
        if (durationEl) {
            if (weekly > 0) {
                const weeks = result.total / weekly;
                durationEl.textContent =
                    "At " + weekly.toLocaleString() + " visitors/week → about " +
                    weeks.toFixed(1) + " weeks";
                durationEl.hidden = false;
            } else {
                durationEl.hidden = true;
            }
        }
    }

    function useSuggestedMde(mode) {
        const last = window.__lastApply;
        if (!last) return;
        const mdeInput = document.getElementById("size-mde");
        const modeSelect = document.getElementById("size-mde-mode");
        if (!mdeInput || !modeSelect) return;

        if (mode === "relative") {
            modeSelect.value = "relative_pct";
            mdeInput.value = last.suggestedMdeRel.toFixed(2);
        } else {
            modeSelect.value = "absolute_pp";
            mdeInput.value = Math.abs(last.suggestedMdePp).toFixed(2);
        }
        switchTab("sample-size");
        updateSizeTab();
    }

    function switchTab(tabId) {
        document.querySelectorAll(".tool-tab").forEach(function (btn) {
            btn.classList.toggle("active", btn.dataset.tab === tabId);
        });
        document.querySelectorAll(".tool-panel").forEach(function (panel) {
            panel.hidden = panel.id !== "panel-" + tabId;
        });
    }

    function bindTabs() {
        document.querySelectorAll(".tool-tab").forEach(function (btn) {
            btn.addEventListener("click", function () {
                switchTab(btn.dataset.tab);
            });
        });
    }

    function bindInputs() {
        ["apply-baseline", "apply-min", "apply-max", "apply-unit", "apply-direction"].forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.addEventListener("input", updateApplyTab);
            if (el) el.addEventListener("change", updateApplyTab);
        });
        ["size-baseline", "size-mde", "size-mde-mode", "size-alpha", "size-power", "size-direction", "size-weekly"].forEach(function (id) {
            const el = document.getElementById(id);
            if (el) el.addEventListener("input", updateSizeTab);
            if (el) el.addEventListener("change", updateSizeTab);
        });

        document.getElementById("btn-use-mde-pp")?.addEventListener("click", function () {
            useSuggestedMde("pp");
        });
        document.getElementById("btn-use-mde-rel")?.addEventListener("click", function () {
            useSuggestedMde("relative");
        });
    }

    function prefillFromQuery() {
        const q = readQuery();
        showSourceCard(q);

        if (q.baseline != null && q.baseline !== "") {
            const b = document.getElementById("apply-baseline");
            if (b) b.value = q.baseline;
        }
        if (q.min != null && q.min !== "") {
            const el = document.getElementById("apply-min");
            if (el) el.value = q.min;
        }
        if (q.max != null && q.max !== "") {
            const el = document.getElementById("apply-max");
            if (el) el.value = q.max;
        }
        const unitEl = document.getElementById("apply-unit");
        if (unitEl && q.unit) unitEl.value = q.unit;
        const dirEl = document.getElementById("apply-direction");
        if (dirEl && q.direction) dirEl.value = q.direction;

        if (window.location.search.includes("tab=sample-size")) {
            switchTab("sample-size");
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        bindTabs();
        bindInputs();
        prefillFromQuery();
        updateApplyTab();
        updateSizeTab();
    });
})();
