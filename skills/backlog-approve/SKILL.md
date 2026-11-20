---
name: backlog-approve
description: Use when the user wants to approve backlog tasks that wait for their OK ("approve the ask-first tasks", "run them tonight", "haan ye kar do") — adds the approved label to chosen issues, or posts "tonight: go" for one night.
---

# Backlog Approve

Let the runner do tasks labelled `ask-first`. Two ways:
- **Approve specific tasks:** add the `approved` label. It stays until removed, so the runner may do them on any run.
- **Tonight only:** comment `tonight: go` on the `tonight` issue, after 18:00 (in the config's `timezone`). All `ask-first` tasks may then run until noon tomorrow, then approval lapses. A comment posted before 18:00 doesn't count.

**GitHub calls:** use `gh api …` (REST). If `gh` is missing or blocked, use the matching GitHub MCP tool (`mcp__github__*`).

## 1. Config

Read `~/backlog-runner/config.json` (or the path the user gives) for `owner`, `repos`, `notes_repo` and `log_repo`. No config in reach → ask for the repo names.

## 2. Find what's waiting

For each repo in `repos` plus `notes_repo`, list open issues with `backlog` + `ask-first`, without `approved`, `runner:done` or `runner:failed`:
```bash
gh api "repos/<repo>/issues?state=open&labels=backlog,ask-first&per_page=100" \
  --jq '[.[] | select(.pull_request == null) | {number, title, url: .html_url, labels: [.labels[].name]}]'
```
Also include `backlog` issues opened by someone other than `owner` without `approved` — the runner skips those until approved too. Mark them "opened by <login>".

Nothing waiting → say so and stop.

## 3. Ask which ones

Show a numbered list (repo, title, link) and ask once: which to approve — all, some (by number), or "tonight only". If the user already said exactly what they want ("approve all", "tonight: go"), skip the question.

For issues opened by someone else, read their body before approving and point out anything risky (secrets, CI changes, deleting things). The user decides.

## 4. Apply

- **Approve:** add the label without removing others:
  `gh api repos/<repo>/issues/<n>/labels -f "labels[]=approved"`
  (MCP: `issue_write` `update` with the existing labels plus `approved`.)
- **Tonight only:** only comments posted after 18:00 (config `timezone`) count. If it's earlier than that now, tell the user and offer to approve the tasks with labels instead, or post the comment after 18:00. Otherwise find the open issue titled exactly `tonight` in `log_repo` and comment `tonight: go`. This must be posted as the user (`owner`) — the runner ignores anyone else. If the tool you'd use would add any extra text to the comment, tell the user and ask them to post `tonight: go` themselves instead.

## 5. Report

Which issues are approved (with links), or that tonight mode is on and until when. Mention that the next scheduled run picks them up, as long as usage is under the floors.
