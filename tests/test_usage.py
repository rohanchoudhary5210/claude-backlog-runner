import json

from runner.usage import DEFAULTS, Decision, gate, load_usage

NOW = 1_800_000_000
DAY = 86400


def write(tmp_path, data):
    p = tmp_path / "u.json"
    p.write_text(data if isinstance(data, str) else json.dumps(data))
    return str(p)


def rl(five=None, seven=None):
    d = {}
    if five:
        d["five_hour"] = {"used_percentage": five[0], "resets_at": five[1]}
    if seven:
        d["seven_day"] = {"used_percentage": seven[0], "resets_at": seven[1]}
    return d


def test_load_missing_file_returns_none(tmp_path):
    assert load_usage(str(tmp_path / "nope.json"), NOW) is None


def test_load_malformed_json_returns_none(tmp_path):
    assert load_usage(write(tmp_path, "{not json"), NOW) is None


def test_load_drops_expired_window(tmp_path):
    u = load_usage(write(tmp_path, rl(five=(10, NOW - 1), seven=(20, NOW + DAY))), NOW)
    assert u.five_hour is None
    assert u.seven_day.used_pct == 20


def test_load_all_expired_returns_none(tmp_path):
    assert load_usage(write(tmp_path, rl(five=(10, NOW - 1), seven=(20, NOW))), NOW) is None


def test_gate_none_is_fallback():
    d = gate(None, DEFAULTS, NOW)
    assert d.go and d.fallback and "no usage data" in d.reason


def load(tmp_path, **kw):
    return load_usage(write(tmp_path, rl(**kw)), NOW)


def test_gate_under_floors_goes(tmp_path):
    d = gate(load(tmp_path, five=(40, NOW + 3600), seven=(50, NOW + 3 * DAY)), DEFAULTS, NOW)
    assert d.go and not d.fallback


def test_gate_weekly_floor_stops(tmp_path):
    d = gate(load(tmp_path, seven=(80.0, NOW + 3 * DAY)), DEFAULTS, NOW)
    assert not d.go and "7-day" in d.reason


def test_gate_near_reset_raises_floor(tmp_path):
    d = gate(load(tmp_path, seven=(90, NOW + 23 * 3600)), DEFAULTS, NOW)
    assert d.go


def test_gate_exactly_24h_uses_normal_floor(tmp_path):
    d = gate(load(tmp_path, seven=(90, NOW + DAY)), DEFAULTS, NOW)
    assert not d.go


def test_gate_five_hour_floor_stops(tmp_path):
    d = gate(load(tmp_path, five=(85, NOW + 3600), seven=(10, NOW + 3 * DAY)), DEFAULTS, NOW)
    assert not d.go and "5-hour" in d.reason


def test_gate_missing_one_window_checks_the_other(tmp_path):
    d = gate(load(tmp_path, seven=(50, NOW + 3 * DAY)), DEFAULTS, NOW)
    assert d == Decision(go=True, fallback=False, reason=d.reason) and d.go
