"""Read Claude usage windows and decide whether a backlog run may continue."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

DEFAULTS = {
    "weekly_floor": 80,
    "weekly_floor_near_reset": 95,
    "near_reset_hours": 24,
    "five_hour_floor": 85,
    "max_tasks": 3,
    "fallback_max_tasks": 1,
    "max_age_minutes": 90,
}

_PCTS = ("weekly_floor", "weekly_floor_near_reset", "five_hour_floor")
_COUNTS = ("near_reset_hours", "max_tasks", "fallback_max_tasks", "max_age_minutes")


def validate_config(cfg: dict) -> list[str]:
    """Return a list of problems; empty means the numeric settings are usable."""
    errs = []
    for k in _PCTS + _COUNTS:
        v = cfg.get(k, DEFAULTS[k])
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            errs.append(f"{k} must be a number")
        elif k in _PCTS and not 0 <= v <= 100:
            errs.append(f"{k} must be 0-100")
        elif k in _COUNTS and (v < 0 or int(v) != v):
            errs.append(f"{k} must be a whole number >= 0")
    return errs


@dataclass
class Window:
    used_pct: float
    resets_at: int


@dataclass
class Usage:
    five_hour: Window | None
    seven_day: Window | None


@dataclass
class Decision:
    go: bool
    fallback: bool
    reason: str


def _window(raw, now: int) -> Window | None:
    try:
        w = Window(float(raw["used_percentage"]), int(raw["resets_at"]))
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(w.used_pct) or not 0 <= w.used_pct <= 100:
        return None
    return w if w.resets_at > now else None


def load_usage(path: str, now: int, max_age_minutes: int = DEFAULTS["max_age_minutes"]) -> Usage | None:
    """Load the saved `rate_limits` object; None if missing, broken, old or fully stale."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    cap = data.get("captured_at")
    if isinstance(cap, bool) or not isinstance(cap, (int, float)) or now - cap > max_age_minutes * 60:
        return None
    u = Usage(_window(data.get("five_hour"), now), _window(data.get("seven_day"), now))
    return u if (u.five_hour or u.seven_day) else None


def gate(usage: Usage | None, cfg: dict, now: int) -> Decision:
    c = {**DEFAULTS, **(cfg or {})}
    if usage is None:
        return Decision(True, True, "no usage data; running fallback task cap")
    sd = usage.seven_day
    if sd:
        near = (sd.resets_at - now) < c["near_reset_hours"] * 3600
        floor = c["weekly_floor_near_reset"] if near else c["weekly_floor"]
        if sd.used_pct >= floor:
            return Decision(False, False, f"7-day usage {sd.used_pct:.0f}% >= floor {floor}%")
    fh = usage.five_hour
    if fh and fh.used_pct >= c["five_hour_floor"]:
        return Decision(False, False, f"5-hour usage {fh.used_pct:.0f}% >= floor {c['five_hour_floor']}%")
    if fh is None:
        return Decision(True, True, "5-hour usage unknown; running fallback task cap")
    return Decision(True, False, "usage under floors")
