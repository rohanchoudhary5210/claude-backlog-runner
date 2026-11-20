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

Issues opened by anyone other than `owner` only run once you add `approved`, even if labelled `safe`. The runner never touches CI/workflow files.

### 2. Config
Copy `config.example.json` → `config.json` and list your repos. Floors are "stop at": 7-day 80% (95% within 24 h of the weekly reset), 5-hour 85%.

### 3. Usage data (statusline hook)
Add to `~/.claude/settings.json` where the runs happen:
```json
"statusLine": { "type": "command", "command": "bash /path/to/claude-backlog-runner/scripts/statusline_capture.sh" }
```
It writes `~/.claude/backlog-runner/usage.json` with a `captured_at` time; data older than `max_age_minutes` (90) is ignored. Without it, each run does at most `fallback_max_tasks` (1) task.

**First thing to check:** in a cloud session, run one prompt then `cat ~/.claude/backlog-runner/usage.json`. If it's missing, cloud sessions don't expose usage yet and the runner stays on the fallback cap.

### 4. Install the skill and schedule it
Put this folder where Claude loads skills (or save it as a skill in Claude), then create scheduled tasks (IST) — e.g. 12:52, 16:24, 00:53, 02:51, 04:52 — with the prompt:

> Run the claude-backlog-runner skill using config at `<path>/config.json`.

## Troubleshooting and known limitations

Problems hit while building and testing the runner, with the fix or workaround for each. Items marked **Open** are not solved yet.

### Design constraints

**Personal use only.** Pooling several people's leftover Claude usage on one shared platform breaks Anthropic's terms: sharing a subscription or using it through a third-party app can get an account banned. So the runner only spends *your own* usage, from *your own* account.

**No official usage API.** Nothing reports how much usage is left. The only source is the Claude Code statusline, which receives `rate_limits` as JSON. That's why `scripts/statusline_capture.sh` exists: it saves that data to `~/.claude/backlog-runner/usage.json` for the gate to read.

### Local setup (Windows)

| Problem | Fix |
|---|---|
| `jq` is "not recognized" | `winget install jqlang.jq`, then open a new terminal. |
| `bash` not found, even with Git Bash installed | Git Bash isn't on `PATH`. Use the full path in the statusline command, e.g. `"C:\\Program Files\\Git\\bin\\bash.exe" C:/path/to/scripts/statusline_capture.sh`. |
| `gh` not installed | `winget install GitHub.cli`, then `gh auth login`. To switch accounts: `gh auth logout`. |
| `claude` not found | Claude Code isn't installed. Install it, then run `claude` once to log in. |
| Bash commands from this README fail in PowerShell | The snippets are Bash. Run them in Git Bash, or rewrite them for PowerShell (e.g. `foreach ($r in @(...)) { ... }` instead of `for r in ...; do ... done`, and a backtick instead of `\` for line breaks). |

### Using Claude Code during setup

- **A prompt pasted into the wrong window is taken literally.** "Give push access" sent to Claude Code was read as "invite a collaborator on GitHub", and it asked for a username. Check which window has focus before pasting.
- **Auto mode blocks access to private repos by default.** Its safety check stops a run from reaching a private repository until you name that repo and allow it explicitly.

### Cloud (scheduled) sessions

| Problem | Status |
|---|---|
| `gh issue …` / `gh pr …` fail: they use GraphQL, which cloud sessions block. | **Fixed.** The skill uses REST (`gh api …`) only. |
| Some cloud sessions allow `gh` for search only, so `gh api` fails too. | **Workaround.** Run each REST call with the matching GitHub MCP tool (`list_issues`, `issue_read`, `create_pull_request` with `draft=true`, `add_issue_comment`, `issue_write`). Plain `git` clone/commit/push works. |
| The issue list for `runner pick` is normally built with `gh api … --jq`. | **Workaround.** Build `/tmp/issues.json` by hand from the MCP output, in the same shape. |
| No usage numbers: the statusline never runs in the cloud, so `usage.json` doesn't exist. | **Open.** The gate returns `fallback: true` and each run does at most `fallback_max_tasks` task(s). |
| The GitHub MCP tools add a "Generated by Claude Code" footer to PR bodies and comments, against the no-attribution rule. | **Open.** Editing a PR body removes it. Editing a comment does not: the footer is added back. |

### Behaviour worth knowing

- **Issues already worked are skipped.** If an issue already has `runner:done`, a `backlog/<n>-*` branch or a PR, the runner leaves it alone, even if a prompt names it. This stops duplicate branches and PRs.
- **`tonight` with no comments means tonight mode is off.** `ask-first` tasks then wait for an `approved` label.

## Development
```bash
python3 -m pytest tests -q && bash tests/test_statusline_capture.sh
```
Python stdlib only; the hook needs `jq`.
