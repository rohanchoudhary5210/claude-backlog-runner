from runner.tasks import select_tasks


def issue(n, *labels, created="2026-11-01T00:00:00Z"):
    return {"number": n, "title": f"t{n}", "url": f"u{n}", "repo": "r/r",
            "createdAt": created, "labels": [{"name": l} for l in labels]}


def nums(xs):
    return [x["number"] for x in xs]


def test_safe_backlog_selected():
    assert nums(select_tasks([issue(1, "backlog", "safe")], False, 3)) == [1]


def test_no_backlog_label_skipped():
    assert select_tasks([issue(1, "safe")], False, 3) == []


def test_ask_first_skipped_without_approval():
    assert select_tasks([issue(1, "backlog", "ask-first")], False, 3) == []


def test_ask_first_with_approved_selected():
    assert nums(select_tasks([issue(1, "backlog", "ask-first", "approved")], False, 3)) == [1]


def test_ask_first_selected_tonight():
    assert nums(select_tasks([issue(1, "backlog", "ask-first")], True, 3)) == [1]


def test_safe_and_ask_first_treated_as_ask_first():
    assert select_tasks([issue(1, "backlog", "safe", "ask-first")], False, 3) == []


def test_done_and_failed_skipped():
    xs = [issue(1, "backlog", "safe", "runner:done"), issue(2, "backlog", "safe", "runner:failed")]
    assert select_tasks(xs, True, 3) == []


def test_priority_then_oldest_order():
    xs = [issue(1, "backlog", "safe", created="2026-01-01T00:00:00Z"),
          issue(2, "backlog", "safe", "priority:2", created="2026-11-01T00:00:00Z"),
          issue(3, "backlog", "safe", "priority:1", created="2026-06-01T00:00:00Z")]
    assert nums(select_tasks(xs, False, 3)) == [3, 2, 1]


def test_limit_respected():
    xs = [issue(i, "backlog", "safe") for i in range(5)]
    assert len(select_tasks(xs, False, 2)) == 2
