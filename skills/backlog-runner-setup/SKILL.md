---
name: backlog-runner-setup
description: Use when the user wants to set up, install or configure the backlog runner (claude-backlog-runner) — creates the GitHub labels and issues, writes the config, adds the usage statusline and schedules the runs, asking only what it can't find out.
---

# Backlog Runner Setup

Do the whole setup for the user. They should only answer a few questions; never hand them a list of manual steps you could do yourself.

`RUNNER_DIR` = the sibling folder `../claude-backlog-runner` next to this file (it holds `config.example.json` and `scripts/statusline_capture.sh`).

**GitHub calls:** use `gh api …` (REST). If `gh` is missing or blocked, use the matching GitHub MCP tool (`mcp__github__*`). If neither works, stop and tell the user to connect GitHub (Cowork) or run `gh auth login` (PC).

## Rules

- Only create things. Never delete or rename labels, issues, repos or branches, and never change repo settings.
- Never overwrite an existing `config.json` or `statusLine` setting without asking first.
- Re-running setup must be safe: skip anything that already exists.

## 1. Find out what you can

- Login, name and id: `gh api user --jq '{login, name, id}'` (MCP: `get_me`).
- Their repos: `gh api "user/repos?per_page=100&sort=pushed" --jq '.[].full_name'`.
- Where you're running: **PC** if you can read and write `~/.claude/`, else **cloud** (Cowork).
- Timezone: on a PC, the system timezone (`timedatectl show -p Timezone --value`, or `[System.TimeZoneInfo]::Local.Id` on Windows, mapped to an IANA name). In the cloud, ask.

## 2. Ask, in one go

Use the question tool if you have one, else one short message:
1. Which repos should the runner work in? Offer their 4 most recently pushed repos as choices.
2. Timezone: confirm the one you found, or ask for it.
3. Schedule: when are they usually away? Suggest "work hours + overnight" (e.g. 13:00 and 02:00).

Use defaults for everything else: notes repo `<login>/backlog-notes`, the numbers in `config.example.json`, `git_name` = their GitHub name (or login), `git_email` = `<id>+<login>@users.noreply.github.com`.

## 3. Notes repo

If `<login>/backlog-notes` doesn't exist (`gh api repos/<login>/backlog-notes` → 404), create it private:
`gh api user/repos -f name=backlog-notes -F private=true -f description="Backlog runner: notes and run log"`.
If you can't create repos here, ask the user to create an empty private repo with that name and continue once it exists.

## 4. Labels

In `backlog-notes` and each chosen repo, create these labels. "Already exists" (HTTP 422) is fine — skip it.

| name | color | description |
|---|---|---|
| `backlog` | `5319e7` | Eligible for backlog runner |
| `safe` | `0e8a16` | Runner may do this unattended |
| `ask-first` | `fbca04` | Needs approval |
| `approved` | `1d76db` | Approved for the runner |
| `runner:done` | `c2e0c6` | Runner finished (see PR) |
| `runner:failed` | `e99695` | Runner couldn't do it |

`gh api repos/<repo>/labels -f name=<name> -f color=<color> -f description="<description>"`

Without `gh`: GitHub creates a missing label when it's first added to an issue, so the runner's labels appear on first use. Tell the user that `backlog`, `safe`, `ask-first` and `approved` will show up once they add them to an issue.

## 5. Control issues

In `backlog-notes`, create each issue only if no open issue has exactly that title:
- `tonight`, body: `Comment "tonight: go" to approve ask-first tasks for one night.`
- `runner-log`, body: `Run summaries.`

`gh api repos/<login>/backlog-notes/issues -f title=<title> -f body="<body>"`

## 6. Config

Build the config from `RUNNER_DIR/config.example.json` with the values from steps 1–2 (`repos` = chosen repos, `notes_repo` and `log_repo` = `<login>/backlog-notes`, `fallback_max_tasks` = 1).

- **PC:** write it to `~/backlog-runner/config.json` (create the folder). Check it: from `RUNNER_DIR`, `python3 -m runner gate --config ~/backlog-runner/config.json` must print JSON whose `reason` doesn't start with `bad config`.
- **Cloud:** keep it for the scheduled prompt in step 8.

## 7. Usage statusline (PC only)

1. Check `jq` and `bash` work (on Windows, find Git Bash: `C:\Program Files\Git\bin\bash.exe`). If one is missing, offer to install it (`winget install jqlang.jq`); if they decline, skip this step and say runs will use the fallback cap.
2. In `~/.claude/settings.json` (create it if missing, keep every other key), set:
   `"statusLine": {"type": "command", "command": "bash <absolute path of RUNNER_DIR>/scripts/statusline_capture.sh"}`
   On Windows use the quoted full Git Bash path instead of `bash`. If a `statusLine` already exists, ask before replacing it.
3. Tell them: restart Claude Code; the statusline should show `5h …% · 7d …%`. The script path contains the plugin version, so re-run this setup after a plugin update.

## 8. Schedule

Prompt for each run:
- **PC:** `Run the claude-backlog-runner skill using config at ~/backlog-runner/config.json.`
- **Cloud:** `Write this JSON to /tmp/config.json: <the config as one line>. Then run the claude-backlog-runner skill with CONFIG=/tmp/config.json.`

If this session has a tool for scheduled tasks, create the tasks at the times from step 2, in their timezone. Otherwise give them the prompt and times to add themselves.

## 9. Offer a test

Ask whether to create a test issue in their first chosen repo: title `Backlog runner test: add a line to README`, body `Append the line "Hello from the backlog runner" to README.md.`, labels `backlog`, `safe`. If yes, create it and offer to run the runner once now.

## 10. Report

Short summary: repos set up, labels and issues created (or already there), where the config is, statusline on/off, the scheduled runs. End with how to add a task: open an issue with `backlog` + `safe`, or `backlog` + `ask-first` to approve first.
