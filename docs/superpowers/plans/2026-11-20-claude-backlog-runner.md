# Claude Backlog Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Claude skill that, when run (by a scheduled cloud task or by hand), spends leftover Claude usage working through GitHub-Issue backlog tasks on branches, within usage floors and hard safety limits.

**Architecture:** The skill is mostly instructions (`SKILL.md`) that Claude follows. The two decisions that must be exact — "is there enough usage to continue?" and "which issues are eligible?" — live in a small, tested Python package (`runner/`) exposed as a CLI that SKILL.md calls. A statusline hook script captures Claude Code's `rate_limits` JSON to a file the CLI reads. GitHub access is via the `gh` CLI.

**Tech Stack:** Python 3 stdlib only (no pip installs), pytest, bash + `jq`, `gh` CLI, Claude Code statusline hook, Claude scheduled tasks.

**Spec:** `docs/superpowers/specs/2026-11-20-claude-backlog-runner-design.md`

## Global Constraints

- Claude sessions only (cloud scheduled runs, Claude Code, Claude app). No third-party harnesses; never read usage via the login token / private endpoints.
- Usage source: Claude Code statusline `rate_limits.five_hour` / `rate_limits.seven_day` → `used_percentage` (0–100), `resets_at` (unix epoch seconds).
- Default floors: 7-day used < 80%, rising to < 95% when weekly `resets_at` is under 24 h away; 5-hour used < 85%.
- No usage data → run at most `fallback_max_tasks` (default 1) and say so in the summary.
- Per-run task cap default 3. Re-check usage before every task.
- Labels: `backlog`, `safe`, `ask-first`, `approved`, `runner:done`, `runner:failed`; night approval via a `tonight` tracking issue with comment `tonight: go`; summaries go to a `runner-log` issue.
- Branch name: `backlog/<issue#>-<slug>`. Output: **draft** PR linked to the issue. Research tasks write markdown in the `backlog-notes` repo.
- Never unattended: merge, push to default branch, close/delete issues, change repo settings, force-push, touch secrets.
- Commits authored as Rohan only — no `Co-Authored-By` or session attribution lines.
- Config format: JSON (`config.json`) — deviation from the spec's `.yml` to stay stdlib-only (spec left schema to the builder).

## Review Focus

1. Usage file is stale (its `resets_at` already passed) → treat as no data → fallback cap, not "0% used, go wild".
2. Usage file missing, empty or malformed JSON → fallback cap with a clear reason; never a crash.
3. Issue carries both `safe` and `ask-first` → treated as `ask-first` (the stricter rule wins).
4. Issue already labelled `runner:done` or `runner:failed` → never picked again.
5. Weekly reset exactly 24 h away → 80% floor applies (the 95% floor only when strictly under 24 h).

---

### Task 0: Spike — does a cloud session report `rate_limits`? (throwaway)

**Files:** none kept.

- [ ] **Step 1:** In a cloud Claude Code session (scheduled-task environment), configure a statusline command that dumps its stdin to `/tmp/statusline.json`, send one prompt, then `cat /tmp/statusline.json | jq .rate_limits`.
- [ ] **Step 2:** Record the result in the spec under Constraints: "Verified YYYY-MM-DD: cloud sessions DO / DO NOT expose rate_limits." If NOT, Tasks 1–5 still ship; the gate simply always takes the fallback path.

---

### Task 1: Usage reading and the gate

**Files:**
- Create: `runner/__init__.py`, `runner/usage.py`
- Test: `tests/test_usage.py`

**Interfaces:**
- Produces:
  - `@dataclass Window(used_pct: float, resets_at: int)`
  - `@dataclass Usage(five_hour: Window | None, seven_day: Window | None)`
  - `load_usage(path: str, now: int) -> Usage | None` — reads the JSON written by Task 3's script (shape: the `rate_limits` object). Drops any window whose `resets_at <= now`. Returns `None` if file missing/unreadable/malformed or both windows dropped.
  - `@dataclass Decision(go: bool, fallback: bool, reason: str)`
  - `gate(usage: Usage | None, cfg: dict, now: int) -> Decision`
  - `DEFAULTS = {"weekly_floor": 80, "weekly_floor_near_reset": 95, "near_reset_hours": 24, "five_hour_floor": 85, "max_tasks": 3, "fallback_max_tasks": 1}`

- [ ] **Step 1: Write failing tests** in `tests/test_usage.py`:
  - `test_load_missing_file_returns_none`
  - `test_load_malformed_json_returns_none` (file contains `{not json`)
  - `test_load_drops_expired_window`: five_hour `resets_at = now-1` → `usage.five_hour is None`, seven_day kept
  - `test_load_all_expired_returns_none`
  - `test_gate_none_is_fallback`: `gate(None, DEFAULTS, now) == Decision(go=True, fallback=True, reason=<contains "no usage data">)`
  - `test_gate_under_floors_goes`: 5h 40%, 7d 50% (reset in 3 days) → `go=True, fallback=False`
  - `test_gate_weekly_floor_stops`: 7d 80.0%, reset in 3 days → `go=False`, reason mentions "7-day"
  - `test_gate_near_reset_raises_floor`: 7d 90%, reset in 23 h → `go=True`
  - `test_gate_exactly_24h_uses_normal_floor`: 7d 90%, reset in exactly 86400 s → `go=False`
  - `test_gate_five_hour_floor_stops`: 5h 85%, 7d 10% → `go=False`, reason mentions "5-hour"
  - `test_gate_missing_one_window_checks_the_other`: only 7d present at 50% → `go=True, fallback=False`
- [ ] **Step 2:** Run `python -m pytest tests/test_usage.py -v` — expect failures (import error).
- [ ] **Step 3:** Implement `runner/usage.py` per Interfaces. Floors are "stop when used ≥ floor". `cfg` keys missing → take from `DEFAULTS`.
- [ ] **Step 4:** Run `python -m pytest tests/test_usage.py -v` — all PASS.
- [ ] **Step 5:** Commit (author Rohan, no attribution trailer): `git add runner tests && git commit -m "feat: usage loading and gate"`

---

### Task 2: Task selection

**Files:**
- Create: `runner/tasks.py`
- Test: `tests/test_tasks.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `select_tasks(issues: list[dict], tonight: bool, limit: int) -> list[dict]`
  - `issues` items are `gh issue list --json number,title,labels,createdAt,url` objects plus a `repo` key (`"owner/name"`); `labels` is `[{"name": str}, ...]`.
  - Eligible: has `backlog`; has neither `runner:done` nor `runner:failed`; and either (`safe` and not `ask-first`) or (`ask-first` and (`approved` or `tonight`)).
  - Order: issues with a `priority:<n>` label first, ascending `n`; then oldest `createdAt` first. Return at most `limit`.

- [ ] **Step 1: Write failing tests** in `tests/test_tasks.py`:
  - `test_safe_backlog_selected`
  - `test_no_backlog_label_skipped`
  - `test_ask_first_skipped_without_approval`
  - `test_ask_first_with_approved_selected`
  - `test_ask_first_selected_tonight`
  - `test_safe_and_ask_first_treated_as_ask_first` (no approval, not tonight → skipped)
  - `test_done_and_failed_skipped`
  - `test_priority_then_oldest_order`: inputs `[old-no-prio, new-priority:2, mid-priority:1]` → `[mid, new, old]`
  - `test_limit_respected`
- [ ] **Step 2:** `python -m pytest tests/test_tasks.py -v` — FAIL.
- [ ] **Step 3:** Implement `select_tasks` per Interfaces.
- [ ] **Step 4:** `python -m pytest tests/test_tasks.py -v` — PASS.
- [ ] **Step 5:** Commit: `git commit -m "feat: backlog task selection"`

---

### Task 3: CLI + statusline capture script

**Files:**
- Create: `runner/__main__.py`, `scripts/statusline_capture.sh`
- Test: `tests/test_cli.py`, `tests/test_statusline_capture.sh`

**Interfaces:**
- Consumes: `load_usage`, `gate`, `DEFAULTS` (Task 1); `select_tasks` (Task 2).
- Produces (used by SKILL.md):
  - `python -m runner gate --usage-file PATH [--config PATH]` → prints `{"go": bool, "fallback": bool, "reason": str, "max_tasks": int}` (`max_tasks` = `fallback_max_tasks` when fallback, else `max_tasks`); exit 0 always.
  - `python -m runner pick --issues PATH --limit N [--tonight]` → prints the selected issues as a JSON array.
  - `scripts/statusline_capture.sh`: reads statusline JSON on stdin; if `.rate_limits` present, writes it to `${BACKLOG_USAGE_FILE:-$HOME/.claude/backlog-runner/usage.json}` (creating the dir); prints one line `5h <pct>% · 7d <pct>%` or `usage n/a`.

- [ ] **Step 1: Write failing tests.**
  - `tests/test_cli.py`: `test_gate_cli_fallback_on_missing_file` (subprocess, asserts `fallback` true and `max_tasks == 1`); `test_pick_cli_outputs_selection` (temp issues file with one safe + one unapproved ask-first → 1 item).
  - `tests/test_statusline_capture.sh`: pipes `{"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":9999999999}}}` with `BACKLOG_USAGE_FILE=$tmp/u.json`; asserts file contains `"five_hour"` and stdout starts with `5h 12`. Second case: input without `rate_limits` → prints `usage n/a`, file not created.
- [ ] **Step 2:** Run `python -m pytest tests/test_cli.py -v` and `bash tests/test_statusline_capture.sh` — FAIL.
- [ ] **Step 3:** Implement with `argparse` and `json`; script uses `jq`.
- [ ] **Step 4:** Both test commands PASS.
- [ ] **Step 5:** Commit: `git commit -m "feat: runner CLI and statusline capture"`

---

### Task 4: The skill (SKILL.md), config and setup docs

**Files:**
- Create: `SKILL.md`, `config.example.json`, `README.md`

**Interfaces:**
- Consumes: CLI commands from Task 3.
- Produces: the skill a session loads by name `claude-backlog-runner`.

- [ ] **Step 1: Write `SKILL.md`** with frontmatter `name: claude-backlog-runner`, description "Use when a scheduled run or the user asks to spend leftover Claude usage on the GitHub backlog." Body, in order:
  1. Setup check: `gh auth status` OK; `git config user.name/email` set to Rohan's values from config; statusline hook installed (point to README).
  2. Gate: run `python -m runner gate`; if `go` false → post summary ("skipped: <reason>") and stop.
  3. Tonight check: does the `tonight` issue (in `config.log_repo`) have a `tonight: go` comment from the owner dated today (IST, after 18:00 yesterday)? → `--tonight`.
  4. Collect: `gh issue list --label backlog --state open --json number,title,labels,createdAt,url` per configured repo, add `repo`, write to a temp file, run `pick --limit <max_tasks>`.
  5. Per task: branch `backlog/<n>-<slug>` from default branch; do the work; run the repo's tests if a test command is obvious; commit (no attribution trailers); `git push -u origin <branch>`; `gh pr create --draft`; comment on issue; label `runner:done` (or `runner:failed` + reason comment). Research tasks: write `notes/<n>-<slug>.md` in `backlog-notes`, same branch/PR flow. Re-run `gate` before the next task.
  6. If spare usage but only unapproved `ask-first` tasks remain: send a push notification listing them.
  7. Summary: comment on `runner-log` issue + push notification: done (links), failed, awaiting approval, usage before/after.
  8. **Hard limits** section, verbatim from Global Constraints.
- [ ] **Step 2: Write `config.example.json`:** `repos` (list of `owner/name`), `notes_repo`, `log_repo`, `git_name`, `git_email`, floors and caps with the Task 1 default values.
- [ ] **Step 3: Write `README.md`:** install the skill; add statusline hook to `~/.claude/settings.json` (`"statusLine": {"type": "command", "command": "bash <path>/scripts/statusline_capture.sh"}`); `gh label create` commands for all six labels per repo; create `tonight` and `runner-log` issues.
- [ ] **Step 4: Verify:** dry-run by hand in a Claude Code session against a test repo with one `safe` issue whose task is "add a line to README" → draft PR exists, issue labelled `runner:done`, summary comment posted, commit has no attribution trailer (`git log -1 --format=%B`).
- [ ] **Step 5:** Commit: `git commit -m "feat: backlog runner skill and setup docs"`

---

### Task 5: Schedule the runs

**Files:** none (scheduled tasks are created in Claude).

- [ ] **Step 1:** Create five scheduled tasks (cron with `CRON_TZ=Asia/Kolkata`): 13:00, 16:30, 01:00, 03:00, 05:00 (jitter a few minutes off the hour). Prompt: "Run the claude-backlog-runner skill using config at <path>."
- [ ] **Step 2: Verify:** fire one manually; confirm a `runner-log` comment appears.
