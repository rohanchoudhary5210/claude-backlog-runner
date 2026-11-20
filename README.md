# Claude Backlog Runner

A Claude skill that spends leftover Claude usage on your low-priority GitHub backlog — on branches and draft PRs only — while you're at work or asleep.

## How it works

1. You add tasks as GitHub issues labelled `backlog` + `safe` (runs unattended) or `backlog` + `ask-first` (runs only once you add `approved`, or on a night you said `tonight: go`).
2. Scheduled Claude runs load this skill, check your remaining usage, and work through eligible issues one at a time.
3. Each finished task becomes a **draft PR**; a summary lands on your `runner-log` issue.

It never merges, never pushes to `main`, never closes issues.

## Quick start

1. Get the skill: clone this repo (or fork it), e.g. `git clone https://github.com/rohanchoudhary5210/claude-backlog-runner ~/.claude/skills/claude-backlog-runner`.
2. `cp config.example.json config.json` and fill in your GitHub login, repos, git name/email and `timezone`.
3. Create the labels and the two issues (below) in your repos.
4. Schedule a Claude task with the prompt: *Run the claude-backlog-runner skill using config at `<path>/config.json`.*
5. Optional: add the statusline hook so the runner can see your usage (otherwise 1 task per run).

## Setup

### 1. Repos and labels
Create a notes repo (e.g. `backlog-notes`) for research/writing tasks and the log. Then, for it and each code repo (replace `<owner>/<repo>`):
```bash
for r in <owner>/backlog-notes <owner>/<code-repo>; do
  gh label create backlog      -R $r -c 5319e7 -d "Eligible for backlog runner" -f
  gh label create safe         -R $r -c 0e8a16 -d "Runner may do this unattended" -f
  gh label create ask-first    -R $r -c fbca04 -d "Needs approval" -f
  gh label create approved     -R $r -c 1d76db -d "Approved for the runner" -f
  gh label create runner:done  -R $r -c c2e0c6 -d "Runner finished (see PR)" -f
  gh label create runner:failed -R $r -c e99695 -d "Runner couldn't do it" -f
done
gh issue create -R <owner>/backlog-notes -t tonight    -b 'Comment "tonight: go" to approve ask-first tasks for one night.'
gh issue create -R <owner>/backlog-notes -t runner-log -b "Run summaries."
```
No `gh` CLI? Create the same labels and issues in the GitHub web UI.

Optional: `priority:1`, `priority:2`, … labels — lower runs first.

Issues opened by anyone other than `owner` only run once you add `approved`, even if labelled `safe`. The runner never touches CI/workflow files.

### 2. Config
Copy `config.example.json` → `config.json` (git-ignored) and fill it in:

| Key | Meaning |
|---|---|
| `owner` | Your GitHub login — only your issues and your `tonight: go` comments count |
| `repos` | Code repos to work in (`owner/name`) |
| `notes_repo`, `log_repo` | Repo for research notes and the `tonight` / `runner-log` issues |
| `git_name`, `git_email` | Commit author (set per clone, never global) |
| `timezone` | IANA zone for the summary time and the "tonight" window (default `Asia/Kolkata`) |
| floors | "Stop at": 7-day 80% (95% within 24 h of the weekly reset), 5-hour 85% |
| `max_tasks`, `fallback_max_tasks` | Tasks per run with / without usage data |

### 3. Usage data (statusline hook)
Add to `~/.claude/settings.json` on the machine where the runs happen:
```json
"statusLine": { "type": "command", "command": "bash /path/to/claude-backlog-runner/scripts/statusline_capture.sh" }
```
It writes `~/.claude/backlog-runner/usage.json` with a `captured_at` time; data older than `max_age_minutes` (90) is ignored. Without it, each run does at most `fallback_max_tasks` (1) task. Cloud sessions don't expose this data, so cloud runs always use the fallback cap.

### 4. Install the skill and schedule it
- **Claude Code (PC):** put this folder at `~/.claude/skills/claude-backlog-runner/`.
- **Claude app / cloud:** save `SKILL.md` as a skill (if your plan allows), connect GitHub, and make sure your repos are in the session's GitHub access. Where `gh` is blocked, the skill uses the GitHub MCP tools instead.

Then create scheduled tasks at quiet hours with the prompt:

> Run the claude-backlog-runner skill using config at `<path>/config.json`.

## Development
```bash
python3 -m pytest tests -q && bash tests/test_statusline_capture.sh
```
Python stdlib only; the hook needs `jq`.
