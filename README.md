# Claude Backlog Runner

A Claude skill that spends leftover Claude usage on your low-priority GitHub backlog — on branches and draft PRs only — while you're at work or asleep.

## How it works

1. You add tasks as GitHub issues labelled `backlog` + `safe` (runs unattended) or `backlog` + `ask-first` (runs only once you add `approved`, or on a night you said `tonight: go`).
2. Scheduled Claude runs load this skill, check your remaining usage, and work through eligible issues one at a time.
3. Each finished task becomes a **draft PR**; a summary lands on your `runner-log` issue.

It never merges, never pushes to `main`, never closes issues.

## Setup

### 1. Repos and labels
Create a `backlog-notes` repo (research/writing tasks + the log). Then, for it and each code repo:
```bash
for r in rohanchoudhary5210/backlog-notes rohanchoudhary5210/Piasa-Dekh; do
  gh label create backlog      -R $r -c 5319e7 -d "Eligible for backlog runner" -f
  gh label create safe         -R $r -c 0e8a16 -d "Runner may do this unattended" -f
  gh label create ask-first    -R $r -c fbca04 -d "Needs approval" -f
  gh label create approved     -R $r -c 1d76db -d "Approved for the runner" -f
  gh label create runner:done  -R $r -c c2e0c6 -d "Runner finished (see PR)" -f
  gh label create runner:failed -R $r -c e99695 -d "Runner couldn't do it" -f
done
gh issue create -R rohanchoudhary5210/backlog-notes -t tonight    -b 'Comment "tonight: go" to approve ask-first tasks for one night.'
gh issue create -R rohanchoudhary5210/backlog-notes -t runner-log -b "Run summaries."
```
Optional: `priority:1`, `priority:2`, … labels — lower runs first.

### 2. Config
Copy `config.example.json` → `config.json` and list your repos. Floors are "stop at": 7-day 80% (95% within 24 h of the weekly reset), 5-hour 85%.

### 3. Usage data (statusline hook)
Add to `~/.claude/settings.json` where the runs happen:
```json
"statusLine": { "type": "command", "command": "bash /path/to/claude-backlog-runner/scripts/statusline_capture.sh" }
```
It writes `~/.claude/backlog-runner/usage.json`. Without it, each run does at most `fallback_max_tasks` (1) task.

**First thing to check:** in a cloud session, run one prompt then `cat ~/.claude/backlog-runner/usage.json`. If it's missing, cloud sessions don't expose usage yet and the runner stays on the fallback cap.

### 4. Install the skill and schedule it
Put this folder where Claude loads skills (or save it as a skill in Claude), then create scheduled tasks (IST) — e.g. 12:52, 16:24, 00:53, 02:51, 04:52 — with the prompt:

> Run the claude-backlog-runner skill using config at `<path>/config.json`.

## Development
```bash
python3 -m pytest tests -q && bash tests/test_statusline_capture.sh
```
Python stdlib only; the hook needs `jq`.
