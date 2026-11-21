"""Run statistics: one hidden line per run summary, totals over recent days."""
from __future__ import annotations

import json
import re

_RE = re.compile(r"<!-- runner-stats (\{.*?\}) -->")


def stats_line(at: int, done: int, failed: int, fallback: bool,
               seven_before: float | None, seven_after: float | None) -> str:
    data = {"at": int(at), "done": int(done), "failed": int(failed), "fallback": bool(fallback),
            "seven_before": seven_before, "seven_after": seven_after}
    return f"<!-- runner-stats {json.dumps(data, separators=(',', ':'))} -->"


def parse_stats(texts: list[str]) -> list[dict]:
    out = []
    for t in texts:
        for m in _RE.finditer(t or ""):
            try:
                d = json.loads(m.group(1))
            except ValueError:
                continue
            if isinstance(d, dict) and isinstance(d.get("at"), int):
                out.append(d)
    return out


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def summarize(stats: list[dict], now: int, days: int = 7) -> dict:
    recent = [s for s in stats if now - s["at"] <= days * 86400]
    used = 0.0
    for s in recent:
        b, a = _num(s.get("seven_before")), _num(s.get("seven_after"))
        if b is not None and a is not None and a > b:
            used += a - b
    return {
        "days": days,
        "runs": len(recent),
        "done": sum(int(s.get("done", 0)) for s in recent),
        "failed": sum(int(s.get("failed", 0)) for s in recent),
        "fallback_runs": sum(1 for s in recent if s.get("fallback")),
        "weekly_pct_used": round(used, 1),
    }
