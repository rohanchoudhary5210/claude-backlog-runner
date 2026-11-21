from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def ts(y, mo, d, h):
    return int(datetime(y, mo, d, h, tzinfo=IST).timestamp())


def c(login, body, y, mo, d, h):
    t = datetime(y, mo, d, h, tzinfo=IST).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"author": {"login": login}, "body": body, "createdAt": t}


def tonight(jq, write, comments, now, offset="+05:30", owner="rohan"):
    f = write("c.json", comments)
    return jq("tonight", "--slurpfile", "comments", f, "--arg", "owner", owner,
              "--arg", "utc_offset", offset, "--argjson", "now", now)["tonight"]


def test_last_night_counts_for_early_run(jq, write):
    assert tonight(jq, write, [c("rohan", "tonight: go", 2026, 11, 20, 23)], ts(2026, 11, 21, 3))


def test_before_previous_evening_ignored(jq, write):
    assert not tonight(jq, write, [c("rohan", "tonight: go", 2026, 11, 20, 10)], ts(2026, 11, 21, 3))


def test_other_author_ignored(jq, write):
    assert not tonight(jq, write, [c("stranger", "tonight: go", 2026, 11, 20, 23)], ts(2026, 11, 21, 3))


def test_afternoon_run_needs_same_day_evening(jq, write):
    assert not tonight(jq, write, [c("rohan", "tonight: go", 2026, 11, 20, 23)], ts(2026, 11, 21, 13))
    assert tonight(jq, write, [c("rohan", "tonight: go", 2026, 11, 21, 18)], ts(2026, 11, 21, 19))


def test_body_rules(jq, write):
    now = ts(2026, 11, 21, 3)
    assert not tonight(jq, write, [c("rohan", "not tonight: go", 2026, 11, 20, 23)], now)
    assert tonight(jq, write, [c("Rohan", "  Tonight: GO please", 2026, 11, 20, 23)], now)


def test_future_or_bad_dates_ignored(jq, write):
    now = ts(2026, 11, 21, 3)
    assert not tonight(jq, write, [c("rohan", "tonight: go", 2026, 11, 21, 5)], now)
    assert not tonight(jq, write, [{"author": {"login": "rohan"}, "body": "tonight: go", "createdAt": "x"}], now)


def test_other_offset(jq, write):
    # London (UTC+00:00): comment 19:00 local on the 20th, run 02:00 local on the 21st
    t = datetime(2026, 11, 20, 19, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    now = int(datetime(2026, 11, 21, 2, tzinfo=timezone.utc).timestamp())
    assert tonight(jq, write, [{"author": {"login": "rohan"}, "body": "tonight: go", "createdAt": t}], now, "+00:00")
