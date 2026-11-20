from datetime import datetime, timezone, timedelta

from runner.tonight import tonight_on

IST = timezone(timedelta(hours=5, minutes=30))


def ts(y, mo, d, h, mi=0):
    return int(datetime(y, mo, d, h, mi, tzinfo=IST).timestamp())


def c(login, body, y, mo, d, h):
    t = datetime(y, mo, d, h, tzinfo=IST).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"author": {"login": login}, "body": body, "createdAt": t}


def test_owner_comment_last_night_counts_for_early_run():
    cs = [c("rohan", "tonight: go", 2026, 11, 20, 23)]
    assert tonight_on(cs, "rohan", ts(2026, 11, 21, 3))


def test_comment_before_previous_evening_ignored():
    cs = [c("rohan", "tonight: go", 2026, 11, 20, 10)]
    assert not tonight_on(cs, "rohan", ts(2026, 11, 21, 3))


def test_other_author_ignored():
    cs = [c("stranger", "tonight: go", 2026, 11, 20, 23)]
    assert not tonight_on(cs, "rohan", ts(2026, 11, 21, 3))


def test_afternoon_run_needs_same_day_evening_comment():
    cs = [c("rohan", "tonight: go", 2026, 11, 20, 23)]
    assert not tonight_on(cs, "rohan", ts(2026, 11, 21, 13))


def test_body_must_start_with_phrase():
    cs = [c("rohan", "not tonight: go", 2026, 11, 20, 23)]
    assert not tonight_on(cs, "rohan", ts(2026, 11, 21, 3))


def test_timezone_moves_the_evening_cutoff():
    # 23:00 IST on Nov 20 is 12:30 New York time: before New York's 18:00 cutoff.
    cs = [c("rohan", "tonight: go", 2026, 11, 20, 23)]
    assert not tonight_on(cs, "rohan", ts(2026, 11, 21, 3), tz="America/New_York")
