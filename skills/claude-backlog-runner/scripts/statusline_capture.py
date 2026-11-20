"""Claude Code statusLine command: saves rate_limits for the backlog runner
and prints a short usage line. Python stdlib only, so it works on Windows
without bash or jq."""
import json
import os
import sys
import time


def main() -> None:
    try:
        rl = json.load(sys.stdin).get("rate_limits")
    except (ValueError, AttributeError):
        rl = None
    if not rl:
        print("usage n/a")
        return
    path = os.environ.get("BACKLOG_USAGE_FILE") or os.path.expanduser("~/.claude/backlog-runner/usage.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w") as f:
        json.dump({**rl, "captured_at": int(time.time())}, f)
    os.replace(path + ".tmp", path)

    def pct(key):
        v = (rl.get(key) or {}).get("used_percentage")
        return "?" if v is None else int(v)

    print(f"5h {pct('five_hour')}% · 7d {pct('seven_day')}%")


if __name__ == "__main__":
    main()
