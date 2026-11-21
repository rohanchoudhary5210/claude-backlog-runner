import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "skills" / "claude-backlog-runner"


def run(*args):
    out = subprocess.run([sys.executable, "-m", "runner", *args], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_gate_cli_fallback_on_missing_file(tmp_path):
    d = run("gate", "--usage-file", str(tmp_path / "missing.json"))
    assert d["go"] is True and d["fallback"] is True and d["max_tasks"] == 1


def test_pick_cli_outputs_selection(tmp_path):
    issues = [
        {"number": 1, "labels": [{"name": "backlog"}, {"name": "safe"}], "createdAt": "a", "repo": "r/r"},
        {"number": 2, "labels": [{"name": "backlog"}, {"name": "ask-first"}], "createdAt": "b", "repo": "r/r"},
    ]
    f = tmp_path / "i.json"
    f.write_text(json.dumps(issues))
    out = run("pick", "--issues", str(f), "--limit", "3")
    assert [i["number"] for i in out] == [1]


def test_gate_cli_bad_config_is_no_go(tmp_path):
    cfg = tmp_path / "c.json"
    cfg.write_text('{"weekly_floor": "80"}')
    d = run("gate", "--usage-file", str(tmp_path / "x.json"), "--config", str(cfg))
    assert d["go"] is False and "bad config" in d["reason"]


def test_gate_cli_missing_config_is_no_go(tmp_path):
    d = run("gate", "--usage-file", str(tmp_path / "x.json"), "--config", str(tmp_path / "nope.json"))
    assert d["go"] is False and "bad config" in d["reason"]


def test_now_prints_local_time():
    out = subprocess.run([sys.executable, "-m", "runner", "now", "--tz", "Asia/Kolkata"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out.endswith(" IST") and len(out) == len("2026-11-20 17:21 IST")


def test_unknown_timezone_gives_clear_error():
    r = subprocess.run([sys.executable, "-m", "runner", "now", "--tz", "Nope/Zone"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode != 0 and "tzdata" in r.stderr


def test_gate_cli_reports_percentages(tmp_path):
    import time as _t
    now = int(_t.time())
    u = tmp_path / "u.json"
    u.write_text(json.dumps({"captured_at": now, "five_hour": {"used_percentage": 10, "resets_at": now + 3600},
                             "seven_day": {"used_percentage": 42.5, "resets_at": now + 3 * 86400}}))
    d = run("gate", "--usage-file", str(u))
    assert d["five_hour_pct"] == 10 and d["seven_day_pct"] == 42.5 and d["task_timeout_minutes"] == 30


def test_gate_cli_bad_timeout_is_no_go(tmp_path):
    cfg = tmp_path / "c.json"
    cfg.write_text('{"task_timeout_minutes": "soon"}')
    d = run("gate", "--usage-file", str(tmp_path / "x.json"), "--config", str(cfg))
    assert d["go"] is False


def test_history_cli(tmp_path):
    from runner.history import stats_line
    import time as _t
    f = tmp_path / "t.json"
    f.write_text(json.dumps([stats_line(at=int(_t.time()), done=1, failed=0, fallback=True,
                                        seven_before=None, seven_after=None)]))
    d = run("history", "--texts", str(f))
    assert d["runs"] == 1 and d["done"] == 1


def test_elapsed_cli():
    import time as _t
    d = run("elapsed", "--since", str(int(_t.time()) - 120), "--limit", "30")
    assert d["over"] is False and d["elapsed_minutes"] == 2
