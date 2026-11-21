"""CLI used by SKILL.md:
  python -m runner gate --usage-file PATH [--config PATH]
  python -m runner pick --issues PATH --limit N [--tonight] [--owner LOGIN]
  python -m runner tonight --comments PATH --owner LOGIN [--tz IANA_ZONE]
  python -m runner elapsed --since EPOCH --limit MINUTES
  python -m runner stats --done N --failed N [--fallback] [--seven-before P] [--seven-after P]
  python -m runner history --texts PATH [--days N]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .clock import elapsed
from .history import parse_stats, stats_line, summarize
from .tasks import select_tasks
from .tonight import DEFAULT_TZ, tonight_on
from .usage import DEFAULTS, gate, load_usage, validate_config

DEFAULT_USAGE_FILE = os.path.expanduser("~/.claude/backlog-runner/usage.json")


def _config(path: str | None) -> dict:
    if not path:
        return {}
    with open(path) as f:
        return json.load(f)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="runner")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate")
    g.add_argument("--usage-file", default=os.environ.get("BACKLOG_USAGE_FILE", DEFAULT_USAGE_FILE))
    g.add_argument("--config")
    k = sub.add_parser("pick")
    k.add_argument("--issues", required=True)
    k.add_argument("--limit", type=int, required=True)
    k.add_argument("--tonight", action="store_true")
    k.add_argument("--owner")
    t = sub.add_parser("tonight")
    t.add_argument("--comments", required=True)
    t.add_argument("--owner", required=True)
    t.add_argument("--tz", default=DEFAULT_TZ)
    n = sub.add_parser("now")  # local time for summaries; no `date`/TZ tricks needed on Windows
    n.add_argument("--tz", default=DEFAULT_TZ)
    e = sub.add_parser("elapsed")
    e.add_argument("--since", type=int, required=True)
    e.add_argument("--limit", type=int, required=True)
    st = sub.add_parser("stats")
    st.add_argument("--done", type=int, required=True)
    st.add_argument("--failed", type=int, required=True)
    st.add_argument("--fallback", action="store_true")
    st.add_argument("--seven-before", type=float)
    st.add_argument("--seven-after", type=float)
    h = sub.add_parser("history")
    h.add_argument("--texts", required=True)
    h.add_argument("--days", type=int, default=7)
    a = p.parse_args(argv)
    now = int(time.time())

    if a.cmd == "gate":
        try:
            user = _config(a.config)
            errs = validate_config(user) if isinstance(user, dict) else ["config must be a JSON object"]
        except (OSError, ValueError) as e:
            errs = [str(e)]
        if errs:
            print(json.dumps({"go": False, "fallback": False, "max_tasks": 0,
                              "reason": "bad config: " + "; ".join(errs)}))
            return 0
        cfg = {**DEFAULTS, **user}
        usage = load_usage(a.usage_file, now, cfg["max_age_minutes"])
        d = gate(usage, cfg, now)
        cap = cfg["fallback_max_tasks"] if d.fallback else cfg["max_tasks"]
        print(json.dumps({
            "go": d.go, "fallback": d.fallback, "reason": d.reason, "max_tasks": cap,
            "five_hour_pct": usage.five_hour.used_pct if usage and usage.five_hour else None,
            "seven_day_pct": usage.seven_day.used_pct if usage and usage.seven_day else None,
            "task_timeout_minutes": cfg["task_timeout_minutes"],
        }))
    elif a.cmd == "pick":
        with open(a.issues) as f:
            issues = json.load(f)
        print(json.dumps(select_tasks(issues, a.tonight, a.limit, a.owner), indent=2))
    elif a.cmd == "tonight":
        with open(a.comments) as f:
            data = json.load(f)
        comments = data.get("comments", []) if isinstance(data, dict) else data
        print(json.dumps({"tonight": tonight_on(comments, a.owner, now, a.tz)}))
    elif a.cmd == "elapsed":
        print(json.dumps(elapsed(a.since, now, a.limit)))
    elif a.cmd == "stats":
        print(stats_line(now, a.done, a.failed, a.fallback, a.seven_before, a.seven_after))
    elif a.cmd == "history":
        with open(a.texts) as f:
            texts = json.load(f)
        print(json.dumps(summarize(parse_stats([t for t in texts if isinstance(t, str)]), now, a.days)))
    elif a.cmd == "now":
        print(datetime.fromtimestamp(now, ZoneInfo(a.tz)).strftime("%Y-%m-%d %H:%M %Z"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ZoneInfoNotFoundError as e:
        # Windows Python ships without time-zone data.
        sys.exit(f"unknown time zone {e}: check `timezone` in the config, and on Windows run `py -3 -m pip install tzdata`")
