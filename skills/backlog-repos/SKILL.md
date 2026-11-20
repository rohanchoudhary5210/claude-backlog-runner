---
name: backlog-repos
description: Use when the user wants to see, add or remove the repos the backlog runner works in ("which repos does the runner use", "add my X repo to the backlog", "remove Y from the runner") — edits the runner config and labels; never deletes anything on GitHub.
---

# Backlog Repos

List, add or remove the code repos in the backlog runner's config.

**GitHub calls:** use `gh api …` (REST). If `gh` is missing or blocked, use the matching GitHub MCP tool (`mcp__github__*`).

## Rules

- "Remove" only takes a repo out of the config. Never delete a GitHub repo, issue, label or branch — if the user asks for that, say this skill doesn't do it and point them to GitHub's repo settings.
- Back up the config before changing it (`config.json.bak` beside it), and keep every other key as it is.

## Find the config

`~/backlog-runner/config.json`, or the path the user gives. No config → suggest the `backlog-runner-setup` skill and stop. In a cloud session there's usually no config file: ask the user to paste their config, make the change, and give back the updated JSON to put in their scheduled-task prompt.

## List

For each repo in `repos`, plus `notes_repo`, count open issues labelled `backlog`:
```bash
gh api "repos/<repo>/issues?state=open&labels=backlog&per_page=100" \
  --jq '[.[] | select(.pull_request == null) | [.labels[].name]]'
```
From the label lists, count: **pending** (`safe`, or `ask-first` + `approved`, without `runner:done`/`runner:failed`), **waiting approval** (`ask-first` without `approved`), **done** (`runner:done`), **failed** (`runner:failed`). Show one line per repo:
```
owner/app        3 pending · 1 waiting approval · 5 done · 0 failed
owner/backlog-notes (notes)  1 pending · …
```
If a repo can't be read (404/403), say so on its line — it may be renamed, deleted or outside GitHub access.

## Add

1. Accept `owner/name`, a GitHub URL or a loose name; resolve a loose name against `gh api "user/repos?per_page=100" --jq '.[].full_name'` and ask if more than one matches.
2. Check it exists and is reachable: `gh api repos/<repo> --jq .full_name`.
3. Skip it if it's already in `repos`.
4. Create the runner labels there; "already exists" (HTTP 422) is fine:

   | name | color | description |
   |---|---|---|
   | `backlog` | `5319e7` | Eligible for backlog runner |
   | `safe` | `0e8a16` | Runner may do this unattended |
   | `ask-first` | `fbca04` | Needs approval |
   | `approved` | `1d76db` | Approved for the runner |
   | `runner:done` | `c2e0c6` | Runner finished (see PR) |
   | `runner:failed` | `e99695` | Runner couldn't do it |

   `gh api repos/<repo>/labels -f name=<name> -f color=<color> -f description="<description>"`
5. Append it to `repos` and save.
6. In a cloud session, remind them that the scheduled task's GitHub access must include the new repo.

## Remove

1. Match the repo in `repos` (ask if ambiguous). `notes_repo` can't be removed — it holds the control issues.
2. If it has open `backlog` issues, mention how many: the runner will stop picking them up, but they stay on GitHub. Open draft PRs stay too.
3. Take it out of `repos` and save. Don't touch its issues, labels or branches.

## Report

What changed, then the updated list (as in **List**).
