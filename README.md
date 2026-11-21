# Claude Backlog Runner

A Claude plugin that spends leftover Claude usage on your low-priority GitHub backlog — on branches and draft PRs only — while you're at work or asleep.

## How it works

1. You add tasks as GitHub issues labelled `backlog` + `safe` (runs unattended) or `backlog` + `ask-first` (runs only once you add `approved`, or on a night you said `tonight: go`).
2. Scheduled Claude runs load this skill, check your remaining usage, and work through eligible issues one at a time.
3. Each finished task becomes a **draft PR**; a summary lands on your `runner-log` issue.

It never merges, never pushes to `main`, never closes issues.

## What you need

- A **Claude plan** with Claude Code and/or Cowork. The runner spends *your* leftover usage, so it runs on your own account.
- A **GitHub account** with the repos you want the runner to work in.
- **On a PC (Claude Code):** `git`, [`jq`](https://jqlang.org/download/) 1.6+, and the [`gh` CLI](https://cli.github.com) logged in (`gh auth login`). No Python. Windows users: see [Local setup (Windows)](#local-setup-windows) if a command isn't found.
- **In Cowork (cloud):** GitHub connected to Claude, with your repos included in its access. Nothing to install.

## Easy setup (2 steps, ~5 minutes)

Claude does the setup for you. You only answer 2–3 questions.

**1. Install the plugin.** In Claude Code, run:
```
/plugin marketplace add rohanchoudhary5210/claude-backlog-runner
/plugin install backlog-runner@backlog-runner
```
In Cowork: add the marketplace `rohanchoudhary5210/claude-backlog-runner` in the plugin settings and install **backlog-runner**.

**2. Say: "Set up the backlog runner."**

Claude then asks which repos to use, your timezone and when you're usually away, and does the rest:
- creates a private `backlog-notes` repo, the labels, and the `tonight` and `runner-log` issues;
- writes your config;
- on a PC, turns on usage tracking (the statusline);
- schedules the runs;
- optionally creates a test task and runs it once.

Running it again is safe: it skips anything that already exists. After that, add tasks by just telling Claude, e.g. *"Add to backlog: fix the typo on the login page"* (see [Day-to-day use](#day-to-day-use)).

Prefer to do it by hand, or want to know what each part does? The manual steps are below.

## Manual setup, step by step

Setup takes about 15 minutes. You do steps 1–3 once, step 4 only on a PC, and step 5 to start the runs. Step 6 checks that everything works.

### Step 1: Install the plugin

The repo is a Claude plugin marketplace. Add it, then install the `backlog-runner` plugin from it.

**Claude Code:** run these inside Claude Code:
```
/plugin marketplace add rohanchoudhary5210/claude-backlog-runner
/plugin install backlog-runner@backlog-runner
```

**Cowork:** open the plugin settings, choose to add a marketplace, enter `rohanchoudhary5210/claude-backlog-runner`, then install **backlog-runner**.

**Without plugins:** copy every folder inside [`skills/`](skills) to `~/.claude/skills/` (e.g. `skills/claude-backlog-runner/` → `~/.claude/skills/claude-backlog-runner/`).

The plugin contains six skills. You don't call them by name; Claude picks the right one from what you say:

| Skill | What it does |
|---|---|
| `claude-backlog-runner` | The runner itself: checks usage and works through the backlog. Scheduled runs use this one. |
| `backlog-runner-setup` | Does the whole setup for you ("Set up the backlog runner"). |
| `backlog-add` | Turns tasks in plain words into backlog issues. |
| `backlog-status` | Read-only summary of the backlog and the last run. |
| `backlog-approve` | Approves `ask-first` tasks, or allows them for one night. |
| `backlog-repos` | Lists, adds or removes the repos the runner works in. |

### Step 2: Prepare GitHub (labels and two issues)

The runner takes its to-do list from GitHub issues. Labels tell it which issues it may work on.

**2a. Create a notes repo.** Make a repo called `backlog-notes` (private is fine). It holds research/writing tasks and two control issues. Code tasks stay in your normal code repos.

**2b. Create the labels** in `backlog-notes` and in every code repo you'll list in the config:

| Label | Who adds it | What it means |
|---|---|---|
| `backlog` | You | This issue is a task for the runner. Issues without it are ignored. |
| `safe` | You | The runner may do it without asking. |
| `ask-first` | You | Wait for my OK: runs only after you add `approved`, or on a night you said `tonight: go`. |
| `approved` | You | OK given for an `ask-first` issue (or for an issue someone else opened). |
| `runner:done` | Runner | Finished; the issue links to a draft PR. |
| `runner:failed` | Runner | Couldn't do it; the reason is in the run summary. |
| `priority:1`, `priority:2`, … | You (optional) | Lower number runs first. |
| `template:tests`, `template:docs`, `template:deadcode`, `template:lint` | You (optional) | Use a ready-made task recipe (see [Templates](#templates)); the issue body only needs the scope. |

With the `gh` CLI, this creates all of them (replace `<owner>` and `<code-repo>`, and list as many repos as you need):
```bash
for r in <owner>/backlog-notes <owner>/<code-repo>; do
  gh label create backlog       -R $r -c 5319e7 -d "Eligible for backlog runner" -f
  gh label create safe          -R $r -c 0e8a16 -d "Runner may do this unattended" -f
  gh label create ask-first     -R $r -c fbca04 -d "Needs approval" -f
  gh label create approved      -R $r -c 1d76db -d "Approved for the runner" -f
  gh label create runner:done   -R $r -c c2e0c6 -d "Runner finished (see PR)" -f
  gh label create runner:failed -R $r -c e99695 -d "Runner couldn't do it" -f
  for t in tests docs deadcode lint; do
    gh label create template:$t -R $r -c bfdadc -d "Runner template: $t" -f
  done
done
```
No `gh`? Create them on GitHub: repo → **Issues** → **Labels** → **New label**. The names must match exactly; colours don't matter.

**2c. Create two issues in `backlog-notes`.** The titles must be exactly these:
- **`tonight`**: comment `tonight: go` on it to let the runner do `ask-first` tasks that night. A comment counts from 18:00 that day until noon the next day, in your timezone.
- **`runner-log`**: where each run writes its summary. You read this to see what happened.

```bash
gh issue create -R <owner>/backlog-notes -t tonight    -b 'Comment "tonight: go" to approve ask-first tasks for one night.'
gh issue create -R <owner>/backlog-notes -t runner-log -b "Run summaries."
```

### Step 3: Write your config

Copy [`config.example.json`](plugin/skills/claude-backlog-runner/config.example.json) to a folder of your own, for example `~/backlog-runner/config.json`. **Don't keep it inside the plugin folder:** plugin updates replace that folder, and your config would be lost.

Then fill it in:
```json
{
  "owner": "your-github-login",
  "repos": ["your-github-login/your-code-repo"],
  "notes_repo": "your-github-login/backlog-notes",
  "log_repo": "your-github-login/backlog-notes",
  "git_name": "Your Name",
  "git_email": "your-github-login@users.noreply.github.com",
  "timezone": "Asia/Kolkata",
  "utc_offset": "+05:30",
  "weekly_floor": 80,
  "weekly_floor_near_reset": 95,
  "near_reset_hours": 24,
  "five_hour_floor": 85,
  "max_tasks": 3,
  "fallback_max_tasks": 1,
  "max_age_minutes": 90,
  "task_timeout_minutes": 30,
  "dry_run": false
}
```

| Key | What to put |
|---|---|
| `owner` | Your GitHub login. Issues opened by anyone else run only after you add `approved`, and only your `tonight: go` comments count. |
| `repos` | The code repos the runner may work in, as `owner/name`. |
| `notes_repo` | The repo for research/writing tasks (usually `backlog-notes`). |
| `log_repo` | The repo with the `tonight` and `runner-log` issues (usually also `backlog-notes`). |
| `git_name`, `git_email` | The author of the runner's commits. Use your own name; the `…@users.noreply.github.com` email keeps your real email private. |
| `timezone` | Your [IANA timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), e.g. `Asia/Kolkata`, `Europe/London`. Used when scheduling runs. |
| `utc_offset` | Your offset from UTC, e.g. `+05:30` (India), `+00:00` (London in winter). Used for summary times and the `tonight` window. If your clocks change for daylight saving, update it then (or re-run setup). |
| `weekly_floor` | Stop when your 7-day usage reaches this %. At 80, you always keep 20% for yourself. |
| `weekly_floor_near_reset`, `near_reset_hours` | Within 24 h of the weekly reset, the runner may go up to 95%, since that usage would expire anyway. |
| `five_hour_floor` | Stop when your 5-hour usage reaches this %, so you're never locked out right when you sit down to work. |
| `max_tasks` | Most tasks per run when usage data is available. |
| `fallback_max_tasks` | Most tasks per run when there's no usage data (always the case in Cowork). Keep it small. |
| `max_age_minutes` | Usage data older than this is treated as missing. |
| `task_timeout_minutes` | Time limit per task (see [Time limit per task](#time-limit-per-task)). |
| `dry_run` | `true` = preview only, change nothing (see [Dry run](#dry-run-preview)). |

You can leave the numbers as they are.

### Step 4 (PC only, optional): Let the runner see your usage

Claude has no API that reports how much usage is left. Only Claude Code's **statusline** gets these numbers, so the runner skill includes a tiny `jq` program (`status`, in the "Programs" section of [its SKILL.md](plugin/skills/claude-backlog-runner/SKILL.md)) that shows them and saves them to `~/.claude/backlog-runner/usage.json`. Before each task, the runner reads that file and stops if you're above a floor.

Without this step, the runner still works, but does at most `fallback_max_tasks` per run. Cowork never has this data, so skip this step for cloud-only use.

The easy way is *"Set up the backlog runner"*. By hand:
1. Copy the `status` program from that SKILL.md into `~/.claude/backlog-runner/jq/status.jq`.
2. Add this to `~/.claude/settings.json` (full paths, forward slashes, also on Windows):
   ```json
   "statusLine": { "type": "command", "command": "jq -r -f \"C:/Users/<you>/.claude/backlog-runner/jq/status.jq\" 2> \"C:/Users/<you>/.claude/backlog-runner/usage.json\"" }
   ```
   The program prints the usage line and writes the numbers to its error output, which `2>` saves to the file.
3. Restart Claude Code and send any message. The statusline should show something like `5h 12% · 7d 40%`, and `usage.json` should hold plain JSON. If it starts with `jq.exe :` instead (Windows PowerShell rewrites error output), wrap the command: `cmd /c "jq -r -f <path>/status.jq 2> <path>/usage.json"`. If it shows `usage n/a`, Claude Code hasn't sent usage data yet; send another message.

### Step 5: Schedule the runs

The runner only works when a Claude session starts it, so you schedule sessions for the hours you're away (work hours, overnight). Two or three runs a day is enough. Each run checks your usage first and stops if you're too close to a floor.

**Cowork (cloud, PC can be off):**
1. Create a new scheduled task.
2. Pick when it runs, e.g. daily at 13:00 and 02:00.
3. Use this prompt. A cloud session can't read files on your PC, so the config goes inside the prompt:
   > Write this JSON to `~/backlog-runner/config.json`: `{ …paste your whole config.json here… }`. Then run the claude-backlog-runner skill.
4. Make sure the task's GitHub access includes every repo in your config.

**Claude Code (PC must be on):**
1. Use this prompt:
   > Run the claude-backlog-runner skill using config at `~/backlog-runner/config.json`.
2. Run it on a schedule with Claude Code's scheduling, or paste it yourself whenever you have usage left over.

### Step 6: Try it

1. In one of your code repos, open an issue such as *"Add a Hello line to README"* and add the labels `backlog` and `safe`.
2. Run the prompt from step 5 by hand.
3. You should see:
   - a new branch `backlog/<issue-number>-<title>` and a **draft PR** with the change;
   - the label `runner:done` on the issue;
   - a summary on the `runner-log` issue (in Cowork it's written into the issue's description, not a comment).

If nothing happens, the summary on `runner-log` says why. Also see [Troubleshooting](#troubleshooting-and-known-limitations).

## Day-to-day use

You don't need to open GitHub for the usual things. Tell Claude in your own words:

| You say (for example) | What happens | Skill |
|---|---|---|
| *"Add to backlog: fix the typo on the login screen, and research free icon libraries for Godot."* | Picks the right repo, writes a clear issue for each task (what to do + how to tell it's done), sets `safe` or `ask-first` by risk, shows a one-line preview, then creates them. Skips tasks already in the backlog. | `backlog-add` |
| *"What's the backlog status?"* | Read-only summary: queued tasks, tasks waiting for your OK, failed ones, draft PRs to review, and what the last run did. | `backlog-status` |
| *"Approve the waiting tasks"* / *"Let them run tonight"* | Lists the `ask-first` tasks and adds `approved` to the ones you pick, or comments `tonight: go` (after 18:00) to allow all of them for one night. | `backlog-approve` |
| *"Which repos does the runner use?"* / *"Add my notes-app repo"* / *"Remove old-site from the runner"* | Lists repos with task counts, adds a repo (and its labels) to your config, or takes one out of the config. Never deletes anything on GitHub. | `backlog-repos` |

Still your job:
- **Review the results:** check the draft PRs. The runner never merges, never pushes to `main` and never closes issues; merging is always your call.
- **Stop for a while:** remove the scheduled task, or remove the `backlog` label from issues you want left alone.

Prefer GitHub? Open an issue, label it `backlog` plus `safe` (just do it) or `ask-first` (wait for my OK), and approve with the `approved` label.

### Templates

Add a `template:<name>` label and the runner follows a ready-made recipe (in `plugin/skills/claude-backlog-runner/templates/`). The issue body only needs the scope, e.g. *"src/payments"*:

| Label | Recipe |
|---|---|
| `template:tests` | Add missing tests for current behaviour (no production changes; up to ~10 tests). |
| `template:docs` | Make the docs match the code; lists every change and why. |
| `template:deadcode` | Remove code nothing uses; lists "maybe unused" items it left alone. |
| `template:lint` | Fix lint/formatting with the repo's own tools, no logic changes. |

### Dry run (preview)

Say *"Run the claude-backlog-runner skill — dry run"* (or set `"dry_run": true` in the config). The run checks usage and picks tasks as usual but changes nothing: no branches, PRs, labels or comments. You get a "would do / would skip" list instead. Handy before adding a new repo.

### Time limit per task

Each task gets `task_timeout_minutes` (default 30). If it runs over, the runner stops that task without pushing half-done work, marks it `runner:failed` and asks you to split it.

### Weekly history

Every run summary on `runner-log` ends with a line like *"This week: 9 runs · 14 done · 1 failed · ~12% of weekly usage put to work"*. It's computed from a hidden stats line in each summary, so nothing extra is stored. The usage % is only counted for runs that could see usage data (PC with the statusline); cloud runs count as runs and tasks only.

## Updating

New versions come through the plugin marketplace. In Claude Code:
```
/plugin marketplace update backlog-runner
/plugin install backlog-runner@backlog-runner
```
Your config and the statusline program live outside the plugin folder, so updates don't touch them. Run *"Set up the backlog runner"* again after an update to refresh the statusline program; it skips everything else that's already there.

**Coming from 1.x (Python)?** 2.0 needs `jq` instead of Python. Install `jq`, add `"utc_offset"` to your config (e.g. `"+05:30"`), and re-run setup to switch the statusline to the `jq` version.

## Troubleshooting and known limitations

Problems hit while building and testing the runner, with the fix or workaround for each. Items marked **Open** are not solved yet.

### Design constraints

**Personal use only.** Pooling several people's leftover Claude usage on one shared platform breaks Anthropic's terms: sharing a subscription or using it through a third-party app can get an account banned. So the runner only spends *your own* usage, from *your own* account.

**No official usage API.** Nothing reports how much usage is left. The only source is the Claude Code statusline, which receives `rate_limits` as JSON. That's why the `status` program exists: it saves that data to `~/.claude/backlog-runner/usage.json` for the gate to read.

**No scripts in the plugin.** The plugin directory accepts only Markdown, text, JSON and images from unverified publishers, so 2.0 has no Python. Every exact decision (usage floors, which issues may run, tonight mode, time limit, history) is a small `jq` program written out in the runner's SKILL.md, where anyone can read it; the runner copies them to `~/.claude/backlog-runner/jq/` at the start of each run. The tests in `tests/` (not part of the plugin) run those same programs.

### Local setup (Windows)

| Problem | Fix |
|---|---|
| A tool still "not recognized" right after installing it | The open terminal keeps its old `PATH`. **Close that terminal window (and Claude Code), open a new one**, and run `claude --continue` to resume. The setup skill tries a fresh shell first and tells you when a restart is needed. |
| `jq` "not recognized" | `winget install jqlang.jq`, then open a new terminal. |
| `usage.json` starts with `jq.exe :` | Windows PowerShell wrapped jq's error output. Wrap the statusline command in `cmd /c "…"` (see Step 4). |
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
| Some cloud sessions allow `gh` for search only, so `gh api` fails too. | **Fixed.** The skills switch to the matching GitHub MCP tools automatically. Plain `git` clone/commit/push works. |
| The issue list for the `pick` program is normally built with `gh api … --jq`. | **Workaround.** Build `~/.claude/backlog-runner/tmp/issues.json` from the MCP output, in the same shape. |
| No usage numbers: the statusline never runs in the cloud, so `usage.json` doesn't exist. | **Open.** The gate returns `fallback: true` and each run does at most `fallback_max_tasks` task(s). |
| The GitHub MCP tools add a "Generated by Claude Code" footer to PR bodies and comments, against the no-attribution rule. | **Fixed.** In that mode the skill edits each new PR body (which removes the footer), posts no issue comments, and writes the run summary into the `runner-log` issue body instead. Editing a comment can't remove the footer; delete old ones by hand. |

### Behaviour worth knowing

- **Issues already worked are skipped.** If an issue already has `runner:done`, a `backlog/<n>-*` branch or a PR, the runner leaves it alone, even if a prompt names it. This stops duplicate branches and PRs.
- **`tonight` with no comments means tonight mode is off.** `ask-first` tasks then wait for an `approved` label.

## Development

The plugin is the [`plugin/`](plugin) folder; that's what gets installed and what to submit to a plugin directory. The repo root holds the marketplace file, this README and the tests.

The tests run the `jq` programs exactly as they appear in the runner's SKILL.md (they need Python 3, pytest and jq; none of this ships with the plugin):
```bash
python3 -m pytest tests -q
```
