import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "claude-backlog-runner" / "scripts" / "statusline_capture.py"


def run(stdin, usage_file):
    env = {**os.environ, "BACKLOG_USAGE_FILE": str(usage_file), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, str(SCRIPT)], input=stdin, capture_output=True,
                          text=True, encoding="utf-8", env=env, check=True).stdout.strip()


def test_writes_usage_and_prints_line(tmp_path):
    f = tmp_path / "sub" / "u.json"
    out = run('{"rate_limits":{"five_hour":{"used_percentage":12.7,"resets_at":9999999999}}}', f)
    data = json.loads(f.read_text())
    assert data["five_hour"]["used_percentage"] == 12.7
    assert "captured_at" in data
    assert out == "5h 12% · 7d ?%"


def test_no_rate_limits_writes_nothing(tmp_path):
    f = tmp_path / "none" / "u.json"
    assert run('{"model":{}}', f) == "usage n/a"
    assert not f.exists()


def test_bad_input(tmp_path):
    assert run("not json", tmp_path / "u.json") == "usage n/a"
