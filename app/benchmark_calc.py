"""Pure functions for the benchmark calculator (mirrored in static JS)."""
from __future__ import annotations

import math
from typing import Any

Z_ALPHA: dict[float, float] = {0.10: 1.645, 0.05: 1.96, 0.01: 2.576}
Z_POWER: dict[float, float] = {0.80: 0.84, 0.90: 1.28, 0.95: 1.645}


def _clamp_pct(value: float) -> float:
    return max(0.0, min(100.0, value))


def apply_benchmark(
    baseline_pct: float,
    effect_min: float | None,
    effect_max: float | None,
    *,
    unit: str = "percent_relative",
    direction: str = "increase",
) -> dict[str, Any]:
    """Apply an insight effect range to a baseline rate (percent 0–100)."""
    baseline = float(baseline_pct)
    lo = float(effect_min if effect_min is not None else 0)
    hi = float(effect_max if effect_max is not None else lo)
    if lo > hi:
        lo, hi = hi, lo

    if unit == "percent_point":
        if direction == "decrease":
            new_lo = baseline - hi
            new_hi = baseline - lo
        else:
            new_lo = baseline + lo
            new_hi = baseline + hi
    elif direction == "decrease":
        new_lo = baseline * (1 - hi / 100)
        new_hi = baseline * (1 - lo / 100)
    else:
        new_lo = baseline * (1 + lo / 100)
        new_hi = baseline * (1 + hi / 100)

    new_lo = _clamp_pct(new_lo)
    new_hi = _clamp_pct(new_hi)
    if new_lo > new_hi:
        new_lo, new_hi = new_hi, new_lo

    abs_lo = new_lo - baseline
    abs_hi = new_hi - baseline
    mid_rate = (new_lo + new_hi) / 2
    mid_lift_rel = ((mid_rate / baseline) - 1) * 100 if baseline > 0 else 0

    return {
        "baseline_pct": baseline,
        "new_lo": round(new_lo, 2),
        "new_hi": round(new_hi, 2),
        "abs_lo": round(abs_lo, 2),
        "abs_hi": round(abs_hi, 2),
        "mid_rate": round(mid_rate, 2),
        "mid_lift_rel": round(mid_lift_rel, 2),
        "suggested_mde_pp": round(abs((abs_lo + abs_hi) / 2), 2),
        "suggested_mde_rel": round((lo + hi) / 2, 2),
    }


def sample_size_per_variant(
    baseline_pct: float,
    mde_value: float,
    *,
    mde_mode: str = "absolute_pp",
    alpha: float = 0.05,
    power: float = 0.80,
    direction: str = "increase",
) -> dict[str, Any] | None:
    """Two-proportion sample size (per variant), simplified planning formula."""
    p1 = baseline_pct / 100.0
    if mde_mode == "relative_pct":
        delta = p1 * (mde_value / 100.0)
    else:
        delta = mde_value / 100.0

    if direction == "decrease":
        delta = -abs(delta)
    else:
        delta = abs(delta)

    p2 = p1 + delta
    if delta == 0 or p1 <= 0 or p1 >= 1 or p2 <= 0 or p2 >= 1:
        return None

    p_bar = (p1 + p2) / 2.0
    z_a = Z_ALPHA.get(alpha, 1.96)
    z_b = Z_POWER.get(power, 0.84)
    n = 2 * ((z_a + z_b) ** 2) * p_bar * (1 - p_bar) / (delta ** 2)
    per_variant = max(1, math.ceil(n))

    return {
        "per_variant": per_variant,
        "total": per_variant * 2,
        "delta_pp": round(delta * 100, 3),
        "p2_pct": round(p2 * 100, 2),
    }


def estimate_weeks(total_visitors: int, weekly_traffic: int) -> float | None:
    if weekly_traffic <= 0:
        return None
    return round(total_visitors / weekly_traffic, 1)
