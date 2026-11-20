"""Pick which backlog issues a run is allowed to work on."""
from __future__ import annotations


def _labels(issue: dict) -> set[str]:
    return {l.get("name", "") for l in issue.get("labels", [])}


def _priority(labels: set[str]) -> int | None:
    vals = []
    for l in labels:
        if l.startswith("priority:"):
            try:
                vals.append(int(l.split(":", 1)[1]))
            except ValueError:
                pass
    return min(vals) if vals else None


def _eligible(labels: set[str], tonight: bool) -> bool:
    if "backlog" not in labels or labels & {"runner:done", "runner:failed"}:
        return False
    if "ask-first" in labels:  # stricter rule wins over `safe`
        return "approved" in labels or tonight
    return "safe" in labels


def _author(issue: dict) -> str:
    a = issue.get("author") or {}
    return (a.get("login") or "").lower()


def select_tasks(issues: list[dict], tonight: bool, limit: int, owner: str | None = None) -> list[dict]:
    """If `owner` is given, issues opened by anyone else run only with `approved`."""
    picked = []
    for i in issues:
        labels = _labels(i)
        if not _eligible(labels, tonight):
            continue
        if owner and _author(i) != owner.lower() and "approved" not in labels:
            continue
        picked.append(i)

    def key(i):
        p = _priority(_labels(i))
        return (p is None, p if p is not None else 0, i.get("createdAt", ""))

    return sorted(picked, key=key)[: max(limit, 0)]
