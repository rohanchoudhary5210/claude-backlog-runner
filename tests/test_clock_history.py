import json

from runner.clock import elapsed
from runner.history import parse_stats, stats_line, summarize

NOW = 1_800_000_000
DAY = 86400


def test_elapsed_under_and_over():
    assert elapsed(NOW - 10 * 60, NOW, 30) == {"elapsed_minutes": 10, "over": False}
    assert elapsed(NOW - 30 * 60, NOW, 30)["over"] is True


def test_stats_line_round_trips():
    line = stats_line(at=NOW, done=2, failed=1, fallback=False, seven_before=40.0, seven_after=46.5)
    assert line.startswith("<!-- runner-stats ") and line.endswith(" -->")
    [s] = parse_stats(["hello\n" + line + "\nbye"])
    assert s["done"] == 2 and s["seven_after"] == 46.5


def test_parse_ignores_garbage():
    assert parse_stats(["no stats here", "<!-- runner-stats {broken -->", ""]) == []


def test_summarize_window_and_usage():
    texts = [
        stats_line(at=NOW - 1 * DAY, done=2, failed=0, fallback=False, seven_before=40, seven_after=46),
        stats_line(at=NOW - 2 * DAY, done=1, failed=1, fallback=True, seven_before=None, seven_after=None),
        stats_line(at=NOW - 9 * DAY, done=5, failed=0, fallback=False, seven_before=10, seven_after=30),
    ]
    s = summarize(parse_stats(texts), NOW, days=7)
    assert s == {"days": 7, "runs": 2, "done": 3, "failed": 1, "fallback_runs": 1, "weekly_pct_used": 6.0}


def test_summarize_ignores_negative_usage_change():
    # weekly window reset between before/after -> don't count negative
    t = [stats_line(at=NOW, done=1, failed=0, fallback=False, seven_before=90, seven_after=2)]
    assert summarize(parse_stats(t), NOW)["weekly_pct_used"] == 0.0
