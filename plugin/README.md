# Backlog Runner (plugin)

Spends your leftover Claude usage on your low-priority GitHub backlog: it works through issues you label `backlog` + `safe` (or approved `ask-first`), one at a time, and leaves each result as a **draft PR**. It never merges, never pushes to the default branch, never closes issues, and never touches CI files.

Install (Claude Code 2.1.275 or later):
```
/plugin install backlog-runner --marketplace rohanchoudhary5210/claude-backlog-runner
```
Then say *"Set up the backlog runner"*.

Skills:
- `backlog-runner-setup`: say *"Set up the backlog runner"* and it creates the labels, the control issues and your config, turns on usage tracking and schedules the runs.
- `claude-backlog-runner`: the runner itself (scheduled, or *"Run the claude-backlog-runner skill"*; add *"dry run"* to preview).
- `backlog-add`, `backlog-status`, `backlog-approve`, `backlog-repos`: add tasks in plain words, see what's happening, approve waiting tasks, manage which repos it uses.

Needs `git`, `gh` and `jq`. No Python, no scripts: every exact check is a small `jq` program written out in `skills/claude-backlog-runner/SKILL.md`.

Full guide: https://github.com/rohanchoudhary5210/claude-backlog-runner
