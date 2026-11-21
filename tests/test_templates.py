from pathlib import Path

from runner.tasks import TEMPLATES, select_tasks, template_for

SKILL = Path(__file__).resolve().parent.parent / "skills" / "claude-backlog-runner"


def lab(*names):
    return {l for l in names}


def test_template_for_known_label():
    assert template_for(lab("backlog", "safe", "template:tests")) == "tests"


def test_template_for_unknown_or_missing():
    assert template_for(lab("backlog", "template:nope")) is None
    assert template_for(lab("backlog")) is None


def test_every_template_has_a_prompt_file():
    for name in TEMPLATES:
        f = SKILL / "templates" / f"{name}.md"
        assert f.is_file() and f.read_text().strip(), name


def test_pick_adds_template_field():
    issue = {"number": 1, "createdAt": "a", "repo": "r/r", "author": {"login": "o"},
             "labels": [{"name": "backlog"}, {"name": "safe"}, {"name": "template:docs"}]}
    plain = {**issue, "number": 2, "labels": [{"name": "backlog"}, {"name": "safe"}]}
    out = {i["number"]: i for i in select_tasks([issue, plain], False, 3, "o")}
    assert out[1]["template"] == "docs" and out[2]["template"] is None
