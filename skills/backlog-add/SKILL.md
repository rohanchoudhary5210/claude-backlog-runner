---
name: backlog-add
description: Use when the user wants to add, queue or note down tasks for the backlog runner to do later ("add to backlog", "backlog mein daal do", "do this later", a pasted list of todos) — turns plain words into labelled GitHub issues in the right repo.
---

# Add to Backlog

Turn the user's plain-language tasks into backlog issues the runner can pick up. The user should only describe the task; you pick the repo, write the issue and set the labels.

**GitHub calls:** use `gh api …` (REST). If `gh` is missing or blocked, use the matching GitHub MCP tool (`mcp__github__*`).

## 1. Load the config

Read `~/backlog-runner/config.json` (or the path the user gives). It has `owner`, `repos` (code repos) and `notes_repo`. If there's no config, ask which repo the tasks go in — and suggest running the `backlog-runner-setup` skill if they haven't set up yet.

## 2. Split and understand the tasks

One message can hold one task or many (a list, lines, or "and also…"). Make one issue per task. For each one decide:

- **Repo:** a code change goes to the code repo it's about. Match names loosely ("paisa dekh app" → `owner/Piasa-Dekh`). If there's only one code repo, use it. Research, reading, comparison or writing tasks go to `notes_repo`. If you can't tell, ask (step 4).
- **Title:** short and imperative, under 70 characters ("Add dark mode toggle to settings screen").
- **Body:** a small ticket the runner can act on without guessing:
  ```
  <What to do, in 1–3 sentences, keeping every detail the user gave.>

  **Done when:** <how to tell it's finished — e.g. "tests pass and the toggle saves the choice">
  ```
  Don't invent requirements. If something important is missing (which file, which screen), ask in step 4 instead of guessing.
- **Approval label:**
  - `safe` — small, low-risk and easy to review: a typo, a README line, a small bug fix, a test, a research note.
  - `ask-first` — anything bigger or riskier: touches many files, deletes code or data, adds or upgrades dependencies, changes auth, payments, secrets or public-facing text, or anything the user called important or said to check first.
  - If the user said "no need to ask" or "check with me", follow that.
- **Priority:** add `priority:1` only if the user said urgent / first / important; otherwise none.

Never add tasks that would need CI/workflow changes or secrets as `safe` — the runner refuses those; mark them `ask-first` and mention they'll need manual work.

## 3. Check for duplicates

For each task, look at open issues in its repo (`gh api "repos/<repo>/issues?state=open&labels=backlog&per_page=100" --jq '.[].title'`). If one already says the same thing, don't create another — point the user to it.

## 4. Confirm once

Show a compact preview and ask a single question, with any open details folded in:

```
1. owner/repo — "Title" — safe
2. owner/backlog-notes — "Title" — ask-first
Add these? (or tell me what to change)
```

Skip the confirmation when the user said to just add them, or when it's one clear `safe` task.

## 5. Create the issues

```bash
gh api repos/<repo>/issues -f title="<title>" -F body=@/tmp/issue_body.md \
  -f "labels[]=backlog" -f "labels[]=<safe|ask-first>" [-f "labels[]=priority:1"] --jq .html_url
```

If a label doesn't exist yet in that repo, GitHub creates it.

## 6. Report

One line per task with its link and label. For `ask-first` tasks, add how to let them run: add the `approved` label, or comment `tonight: go` on the `tonight` issue to approve all of them for one night.
