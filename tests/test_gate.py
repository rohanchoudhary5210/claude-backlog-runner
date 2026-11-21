NOW = 1_800_000_000
DAY = 86400


def usage(five=None, seven=None, captured_at=NOW):
    d = {} if captured_at is None else {"captured_at": captured_at}
    if five:
        d["five_hour"] = {"used_percentage": five[0], "resets_at": five[1]}
    if seven:
        d["seven_day"] = {"used_percentage": seven[0], "resets_at": seven[1]}
    return d


def gate(jq, write, cfg=None, u=None, raw_usage=None):
    args = ["--argjson", "now", NOW, "--slurpfile", "cfg", write("cfg.json", cfg if cfg is not None else {})]
    if raw_usage is not None:
        args += ["--rawfile", "usage", write("u.json", raw_usage)]
    elif u is not None:
        args += ["--rawfile", "usage", write("u.json", u)]
    return jq("gate", *args)


def test_no_usage_file_is_fallback(jq, write):
    d = gate(jq, write)
    assert d["go"] and d["fallback"] and "no usage data" in d["reason"] and d["max_tasks"] == 1


def test_malformed_or_empty_usage_is_fallback(jq, write):
    for raw in ["{not json", "", "[]"]:
        d = gate(jq, write, raw_usage=raw)
        assert d["go"] and d["fallback"], raw


def test_expired_window_dropped(jq, write):
    d = gate(jq, write, u=usage(five=(10, NOW - 1), seven=(20, NOW + DAY)))
    assert d["five_hour_pct"] is None and d["seven_day_pct"] == 20 and d["fallback"]


def test_all_expired_is_fallback(jq, write):
    d = gate(jq, write, u=usage(five=(10, NOW - 1), seven=(20, NOW)))
    assert d["fallback"] and "no usage data" in d["reason"]


def test_old_or_missing_capture_time_is_fallback(jq, write):
    good = dict(five=(10, NOW + 3600), seven=(10, NOW + 3 * DAY))
    assert gate(jq, write, u=usage(**good, captured_at=NOW - 3 * 3600))["fallback"]
    assert gate(jq, write, u=usage(**good, captured_at=None))["fallback"]


def test_nan_or_out_of_range_dropped(jq, write):
    raw = '{"captured_at": %d, "five_hour": {"used_percentage": 150, "resets_at": %d},' \
          ' "seven_day": {"used_percentage": -1, "resets_at": %d}}' % (NOW, NOW + 3600, NOW + DAY)
    assert gate(jq, write, raw_usage=raw)["fallback"]
    nan = '{"captured_at": %d, "five_hour": {"used_percentage": NaN, "resets_at": %d}}' % (NOW, NOW + 3600)
    d = gate(jq, write, raw_usage=nan)
    assert d["go"] and d["fallback"]


def test_under_floors_goes(jq, write):
    d = gate(jq, write, u=usage(five=(40, NOW + 3600), seven=(50, NOW + 3 * DAY)))
    assert d == {"go": True, "fallback": False, "reason": "usage under floors", "max_tasks": 3,
                 "five_hour_pct": 40, "seven_day_pct": 50, "task_timeout_minutes": 30}


def test_weekly_floor_stops(jq, write):
    d = gate(jq, write, u=usage(five=(1, NOW + 3600), seven=(80.0, NOW + 3 * DAY)))
    assert not d["go"] and "7-day" in d["reason"]


def test_near_reset_raises_floor(jq, write):
    assert gate(jq, write, u=usage(five=(1, NOW + 3600), seven=(90, NOW + 23 * 3600)))["go"]


def test_exactly_24h_uses_normal_floor(jq, write):
    assert not gate(jq, write, u=usage(five=(1, NOW + 3600), seven=(90, NOW + DAY)))["go"]


def test_five_hour_floor_stops(jq, write):
    d = gate(jq, write, u=usage(five=(85, NOW + 3600), seven=(10, NOW + 3 * DAY)))
    assert not d["go"] and "5-hour" in d["reason"]


def test_weekly_stop_wins_over_missing_five_hour(jq, write):
    assert not gate(jq, write, u=usage(seven=(90, NOW + 3 * DAY)))["go"]


def test_missing_five_hour_window_is_fallback(jq, write):
    d = gate(jq, write, u=usage(seven=(50, NOW + 3 * DAY)))
    assert d["go"] and d["fallback"]


def test_bad_config_is_no_go(jq, write):
    for cfg in [{"weekly_floor": "80"}, {"weekly_floor": 800}, {"max_tasks": -1}, {"max_tasks": 1.5},
                {"task_timeout_minutes": "soon"}, {"weekly_floor": True}, {"utc_offset": "IST"}, []]:
        d = gate(jq, write, cfg=cfg)
        assert d["go"] is False and d["reason"].startswith("bad config"), cfg


def test_config_values_used(jq, write):
    d = gate(jq, write, cfg={"fallback_max_tasks": 2, "task_timeout_minutes": 45, "utc_offset": "+05:30"})
    assert d["max_tasks"] == 2 and d["task_timeout_minutes"] == 45


def test_missing_config_file_errors(jq, tmp_path):
    p = jq("gate", "--slurpfile", "cfg", tmp_path / "nope.json", check=False)
    assert p.returncode != 0  # SKILL.md: any jq error => go: false
