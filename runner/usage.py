"""Read Claude usage windows and decide whether a backlog run may continue."""
from __future__ import annotations

import json
from dataclasses import dataclass

DEFAULTS = {
    "weekly_floor": 80,
    "weekly_floor_near_reset": 95,
    "near_reset_hours": 24,
    "five_hour_floor": 85,
    "max_tasks": 3,
    "fallback_max_tasks": 1,
}


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
    except (KeyError, TypeError, ValueError):
        return None
    return w if w.resets_at > now else None


def load_usage(path: str, now: int) -> Usage | None:
    """Load the saved `rate_limits` object; None if missing, broken or fully stale."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
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
    return Decision(True, False, "usage under floors")
