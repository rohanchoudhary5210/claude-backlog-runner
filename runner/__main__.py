"""CLI used by SKILL.md:
  python -m runner gate --usage-file PATH [--config PATH]
  python -m runner pick --issues PATH --limit N [--tonight] [--owner LOGIN]
  python -m runner tonight --comments PATH --owner LOGIN [--tz IANA_ZONE]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

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
        d = gate(load_usage(a.usage_file, now, cfg["max_age_minutes"]), cfg, now)
        cap = cfg["fallback_max_tasks"] if d.fallback else cfg["max_tasks"]
        print(json.dumps({"go": d.go, "fallback": d.fallback, "reason": d.reason, "max_tasks": cap}))
    elif a.cmd == "pick":
        with open(a.issues) as f:
            issues = json.load(f)
        print(json.dumps(select_tasks(issues, a.tonight, a.limit, a.owner), indent=2))
    elif a.cmd == "tonight":
        with open(a.comments) as f:
            data = json.load(f)
        comments = data.get("comments", []) if isinstance(data, dict) else data
        print(json.dumps({"tonight": tonight_on(comments, a.owner, now, a.tz)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
