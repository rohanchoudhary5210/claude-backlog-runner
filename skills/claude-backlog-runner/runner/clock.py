"""Per-task time limit: how long a task has been running."""
from __future__ import annotations


def elapsed(since: int, now: int, limit_minutes: int) -> dict:
    mins = max(0, (now - since) // 60)
    return {"elapsed_minutes": int(mins), "over": mins >= limit_minutes}
