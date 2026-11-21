import json
import re

from conftest import SKILL_DIR, programs

NOW = 1_800_000_000
DAY = 86400


def test_all_programs_present():
    assert set(programs()) == {"gate", "pick", "tonight", "elapsed", "stats", "history", "now", "status"}


def test_elapsed(jq):
    assert jq("elapsed", "--argjson", "since", NOW - 600, "--argjson", "limit", 30, "--argjson", "now", NOW) == \
        {"elapsed_minutes": 10, "over": False}
    assert jq("elapsed", "--argjson", "since", NOW - 1800, "--argjson", "limit", 30, "--argjson", "now", NOW)["over"]


def stats(jq, at, done, failed, fallback, before, after):
    return jq("stats", "--argjson", "done", done, "--argjson", "failed", failed, "--argjson", "fallback",
              json.dumps(fallback), "--argjson", "before", json.dumps(before), "--argjson", "after",
              json.dumps(after), "--argjson", "now", at, raw=True)


def history(jq, write, texts, days=7):
    return jq("history", "--slurpfile", "texts", write("t.json", texts), "--argjson", "days", days,
              "--argjson", "now", NOW)


def test_stats_line_format(jq):
    line = stats(jq, NOW, 2, 1, False, 40.0, 46.5)
    assert line.startswith("<!-- runner-stats {") and line.endswith("} -->")


def test_history_window_and_usage(jq, write):
    texts = ["x\n" + stats(jq, NOW - DAY, 2, 0, False, 40, 46),
             stats(jq, NOW - 2 * DAY, 1, 1, True, None, None),
             stats(jq, NOW - 9 * DAY, 5, 0, False, 10, 30),
             stats(jq, NOW, 1, 0, False, 90, 2),          # weekly reset in between: not counted
             "no stats", "<!-- runner-stats {broken -->", ""]
    assert history(jq, write, texts) == {"days": 7, "runs": 3, "done": 4, "failed": 1,
                                        "fallback_runs": 1, "weekly_pct_used": 6.0}


def test_history_many_in_one_text(jq, write):
    body = "\n".join(stats(jq, NOW - i * 3600, 1, 0, False, None, None) for i in range(3))
    assert history(jq, write, [body])["runs"] == 3


def test_now_format(jq):
    out = jq("now", "--arg", "utc_offset", "+05:30", raw=True)
    assert re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d UTC\+05:30", out)


def test_status_saves_and_prints(jq, tmp_path):
    import subprocess
    prog = tmp_path / "status.jq"
    prog.write_text(programs()["status"], encoding="utf-8")
    inp = json.dumps({"rate_limits": {"five_hour": {"used_percentage": 12.7, "resets_at": 9999999999},
                                      "seven_day": {"used_percentage": 40, "resets_at": 9999999999}}})
    p = subprocess.run(["jq", "-r", "-f", str(prog)], input=inp, capture_output=True, text=True)
    assert p.stdout.strip() == "5h 12% · 7d 40%"
    saved = json.loads(p.stderr)
    assert saved["five_hour"]["used_percentage"] == 12.7 and isinstance(saved["captured_at"], int)
    p = subprocess.run(["jq", "-r", "-f", str(prog)], input='{"model": {}}', capture_output=True, text=True)
    assert p.stdout.strip() == "usage n/a" and p.stderr == ""


def test_status_output_feeds_gate(jq, write, tmp_path):
    import subprocess, time
    prog = tmp_path / "status.jq"
    prog.write_text(programs()["status"], encoding="utf-8")
    now = int(time.time())
    inp = json.dumps({"rate_limits": {"five_hour": {"used_percentage": 5, "resets_at": now + 3600},
                                      "seven_day": {"used_percentage": 20, "resets_at": now + 3 * DAY}}})
    saved = subprocess.run(["jq", "-r", "-f", str(prog)], input=inp, capture_output=True, text=True).stderr
    d = jq("gate", "--slurpfile", "cfg", write("c.json", {}), "--rawfile", "usage", write("u.json", saved))
    assert d["go"] and not d["fallback"] and d["seven_day_pct"] == 20


def test_every_template_has_a_prompt_file():
    for name in ("tests", "docs", "deadcode", "lint"):
        f = SKILL_DIR / "templates" / f"{name}.md"
        assert f.is_file() and f.read_text(encoding="utf-8").strip(), name
