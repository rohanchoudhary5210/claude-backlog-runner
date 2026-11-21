import json


def issue(n, *labels, created="2026-11-01T00:00:00Z", author="rohan"):
    return {"number": n, "title": f"t{n}", "url": f"u{n}", "repo": "r/r", "author": {"login": author},
            "createdAt": created, "labels": [{"name": l} for l in labels]}


def pick(jq, write, issues, tonight=False, limit=3, owner=""):
    f = write("issues.json", issues)
    out = jq("pick", "--slurpfile", "issues", f, "--argjson", "limit", limit,
             "--argjson", "tonight", json.dumps(tonight), "--arg", "owner", owner)
    return out


def nums(xs):
    return [x["number"] for x in xs]


def test_safe_backlog_selected(jq, write):
    assert nums(pick(jq, write, [issue(1, "backlog", "safe")])) == [1]


def test_no_backlog_label_skipped(jq, write):
    assert pick(jq, write, [issue(1, "safe")]) == []


def test_ask_first_needs_approval_or_tonight(jq, write):
    assert pick(jq, write, [issue(1, "backlog", "ask-first")]) == []
    assert nums(pick(jq, write, [issue(1, "backlog", "ask-first", "approved")])) == [1]
    assert nums(pick(jq, write, [issue(1, "backlog", "ask-first")], tonight=True)) == [1]


def test_safe_and_ask_first_treated_as_ask_first(jq, write):
    assert pick(jq, write, [issue(1, "backlog", "safe", "ask-first")]) == []


def test_done_and_failed_skipped(jq, write):
    xs = [issue(1, "backlog", "safe", "runner:done"), issue(2, "backlog", "safe", "runner:failed")]
    assert pick(jq, write, xs, tonight=True) == []


def test_priority_then_oldest_order(jq, write):
    xs = [issue(1, "backlog", "safe", created="2026-01-01T00:00:00Z"),
          issue(2, "backlog", "safe", "priority:2", created="2026-11-01T00:00:00Z"),
          issue(3, "backlog", "safe", "priority:1", created="2026-06-01T00:00:00Z"),
          issue(4, "backlog", "safe", "priority:x", created="2025-01-01T00:00:00Z")]
    assert nums(pick(jq, write, xs, limit=4)) == [3, 2, 4, 1]


def test_limit_respected(jq, write):
    xs = [issue(i, "backlog", "safe") for i in range(5)]
    assert len(pick(jq, write, xs, limit=2)) == 2
    assert pick(jq, write, xs, limit=0) == []


def test_non_owner_needs_approval(jq, write):
    xs = [issue(1, "backlog", "safe", author="stranger")]
    assert pick(jq, write, xs, owner="rohan") == []
    assert pick(jq, write, xs, owner="rohan", tonight=True) == []
    assert nums(pick(jq, write, [issue(1, "backlog", "safe", "approved", author="stranger")], owner="rohan")) == [1]


def test_owner_check_case_insensitive(jq, write):
    assert nums(pick(jq, write, [issue(1, "backlog", "safe", author="Rohan")], owner="rohan")) == [1]


def test_template_field(jq, write):
    xs = [issue(1, "backlog", "safe", "template:docs"), issue(2, "backlog", "safe"),
          issue(3, "backlog", "safe", "template:nope")]
    out = {i["number"]: i["template"] for i in pick(jq, write, xs)}
    assert out == {1: "docs", 2: None, 3: None}
