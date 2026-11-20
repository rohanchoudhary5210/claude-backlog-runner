import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
