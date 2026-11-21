import json
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "plugin" / "skills" / "claude-backlog-runner"
SKILL_MD = SKILL_DIR / "SKILL.md"


def programs() -> dict:
    """The jq programs exactly as SKILL.md gives them to the runner."""
    text = SKILL_MD.read_text(encoding="utf-8")
    return dict(re.findall(r"<!-- jq:(\w+) -->\n```jq\n(.*?)\n```", text, re.S))


@pytest.fixture
def jq(tmp_path):
    progs = programs()

    def run(name, *args, stdin=None, raw=False, check=True):
        f = tmp_path / f"{name}.jq"
        f.write_text(progs[name], encoding="utf-8")
        cmd = ["jq"] + (["-r"] if raw else []) + ([] if stdin is not None else ["-n"]) + ["-f", str(f), *map(str, args)]
        p = subprocess.run(cmd, input=stdin, capture_output=True, text=True)
        if not check:
            return p
        assert p.returncode == 0, p.stderr
        return p.stdout.strip() if raw else json.loads(p.stdout)

    return run


@pytest.fixture
def write(tmp_path):
    def w(name, data):
        p = tmp_path / name
        p.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
        return p
    return w
