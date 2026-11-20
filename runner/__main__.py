"""CLI used by SKILL.md:
  python -m runner gate --usage-file PATH [--config PATH]
  python -m runner pick --issues PATH --limit N [--tonight]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from .tasks import select_tasks
from .usage import DEFAULTS, gate, load_usage

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
    a = p.parse_args(argv)

    if a.cmd == "gate":
        cfg = {**DEFAULTS, **_config(a.config)}
        d = gate(load_usage(a.usage_file, int(time.time())), cfg, int(time.time()))
        cap = cfg["fallback_max_tasks"] if d.fallback else cfg["max_tasks"]
        print(json.dumps({"go": d.go, "fallback": d.fallback, "reason": d.reason, "max_tasks": cap}))
    else:
        with open(a.issues) as f:
            issues = json.load(f)
        print(json.dumps(select_tasks(issues, a.tonight, a.limit), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
