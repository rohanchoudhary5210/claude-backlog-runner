---
name: backlog-status
description: Use when the user asks how their backlog or the backlog runner is doing ("backlog ka kya haal hai", "what did the runner do", "anything to review?") — read-only summary of pending tasks, approvals, open draft PRs and the last run.
---

# Backlog Status

A short, read-only report. Change nothing.

**GitHub calls:** use `gh api …` (REST). If `gh` is missing or blocked, use the matching GitHub MCP tool (`mcp__github__*`).

## 1. Config

Read `~/backlog-runner/config.json` (or the path the user gives) for `owner`, `repos`, `notes_repo` and `log_repo`. No config in reach → ask for the repo names, or suggest `backlog-runner-setup`.

## 2. Gather

For each repo in `repos` plus `notes_repo`:
- Open `backlog` issues: `gh api "repos/<repo>/issues?state=open&labels=backlog&per_page=100" --jq '[.[] | select(.pull_request == null) | {number, title, url: .html_url, labels: [.labels[].name]}]'`
- Open runner PRs: `gh api "repos/<repo>/pulls?state=open&per_page=100" --jq '[.[] | select(.head.ref | startswith("backlog/")) | {number, title, url: .html_url, created_at}]'`

Sort the issues into:
- **Queued:** `safe`, or `ask-first` + `approved`, without `runner:done`/`runner:failed`.
- **Waiting for approval:** `ask-first` without `approved`.
- **Failed:** `runner:failed`.
- **Done, PR to review:** `runner:done`, matched with the open PRs.

Last run: the newest entry on the `runner-log` issue in `log_repo` — its latest comment, or the top of the issue body if summaries are written there. Note its time and its usage line. If it has a `This week:` line, show it as is.

Usage (PC only, optional): if `~/.claude/backlog-runner/usage.json` exists, run the gate from the `claude-backlog-runner` skill folder: `python3 -m runner gate --config <config>` (`py -3` on Windows), and report its `reason`.

## 3. Report

Keep it short; list item titles only where the user needs to act:

```
Backlog: 4 queued · 2 waiting approval · 1 failed
To review: 3 draft PRs
  - <title> — <PR link>
Waiting for your OK:
  - <title> — <issue link>
Failed:
  - <title> — <issue link> (<reason from the run log, if any>)
Last run: <time> — <done/failed counts>; usage: <reason>
```

End with the one next step that matters most: review the oldest PR, approve the waiting tasks (the `backlog-approve` skill can do it), or add tasks if the queue is empty.
