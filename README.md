# Claude Backlog Runner

A Claude skill that spends leftover Claude usage on your low-priority GitHub backlog — on branches and draft PRs only — while you're at work or asleep.

## How it works

1. You add tasks as GitHub issues labelled `backlog` + `safe` (runs unattended) or `backlog` + `ask-first` (runs only once you add `approved`, or on a night you said `tonight: go`).
2. Scheduled Claude runs load this skill, check your remaining usage, and work through eligible issues one at a time.
3. Each finished task becomes a **draft PR**; a summary lands on your `runner-log` issue.

It never merges, never pushes to `main`, never closes issues.

## Quick start

1. Install the plugin (Claude Code or Cowork): add the marketplace `rohanchoudhary5210/claude-backlog-runner`, then install `backlog-runner`. In Claude Code:
   ```
   /plugin marketplace add rohanchoudhary5210/claude-backlog-runner
   /plugin install backlog-runner@backlog-runner
   ```
2. Copy [`config.example.json`](skills/claude-backlog-runner/config.example.json) to a folder of your own (e.g. `~/backlog-runner/config.json`) and fill in your GitHub login, repos, git name/email and `timezone`. Keep it outside the plugin folder: plugin updates replace that folder.
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
Copy [`config.example.json`](skills/claude-backlog-runner/config.example.json) to `config.json` outside the plugin folder and fill it in:

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
"statusLine": { "type": "command", "command": "bash /path/to/claude-backlog-runner/skills/claude-backlog-runner/scripts/statusline_capture.sh" }
```
It writes `~/.claude/backlog-runner/usage.json` with a `captured_at` time; data older than `max_age_minutes` (90) is ignored. Without it, each run does at most `fallback_max_tasks` (1) task. Cloud sessions don't expose this data, so cloud runs always use the fallback cap.

### 4. Install the skill and schedule it
- **Plugin (recommended):** add this repo as a plugin marketplace and install `backlog-runner` (see Quick start).
- **Without plugins:** copy `skills/claude-backlog-runner/` to `~/.claude/skills/claude-backlog-runner/`.
- **Claude app / cloud:** install the plugin, or save that folder as a skill (if your plan allows), connect GitHub, and make sure your repos are in the session's GitHub access. Where `gh` is blocked, the skill uses the GitHub MCP tools instead.

Then create scheduled tasks at quiet hours with the prompt:

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
| `bash` not found, even with Git Bash installed | Git Bash isn't on `PATH`. Use the full path in the statusline command, e.g. `"C:\\Program Files\\Git\\bin\\bash.exe" C:/path/to/skills/claude-backlog-runner/scripts/statusline_capture.sh`. |
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
| The GitHub MCP tools add a "Generated by Claude Code" footer to PR bodies and comments, against the no-attribution rule. | **Fixed.** In that mode the skill edits each new PR body (which removes the footer), posts no issue comments, and writes the run summary into the `runner-log` issue body instead. Editing a comment can't remove the footer; delete old ones by hand. |

### Behaviour worth knowing

- **Issues already worked are skipped.** If an issue already has `runner:done`, a `backlog/<n>-*` branch or a PR, the runner leaves it alone, even if a prompt names it. This stops duplicate branches and PRs.
- **`tonight` with no comments means tonight mode is off.** `ask-first` tasks then wait for an `approved` label.

## Development
```bash
python3 -m pytest tests -q && bash tests/test_statusline_capture.sh
```
Python stdlib only; the hook needs `jq`.
