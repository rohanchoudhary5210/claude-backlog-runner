# Claude Backlog Runner — Design

*2026-11-20 · Rohan Choudhary · status: draft for approval*

## Intent

Rohan's Claude plan (5-hour and 7-day usage windows) often resets with capacity unspent — while he's at the office or asleep. This is a personal tool that spends that leftover usage on a backlog of non-priority tasks, instead of letting it expire. It's packaged as a **Claude skill**, so any Claude session (a cloud scheduled run, Claude Code, the Claude app) can run the same procedure.

## Goals

- Turn unused Claude usage into finished low-priority work: code changes on branches, research and writing docs.
- Run without Rohan present (daytime while he's at work, overnight while he sleeps), with his PC off.
- Never leave him short: stop before usage drops below a floor he'd want for his own work.
- One clear morning/evening summary of what got done.

## Non-goals (v1)

- Non-Claude agents (Antigravity etc.) — possible later extension.
- Sharing, pooling or reselling usage with anyone. Personal use only.
- Local-PC tasks (D:\ folders). Everything works on GitHub repos.

## Anti-goals (failure even if it "works")

- Touches `main`, merges, closes issues or changes repo settings on its own.
- Eats usage Rohan needed that evening.
- Reads usage via the login token outside Claude's apps (breaks Anthropic's terms).
- Adds Claude co-author/session lines to commits — commits are authored by Rohan only.

## Constraints

- Must run inside Claude's own apps (scheduled tasks / Claude Code). Third-party harnesses can't use subscription limits.
- Usage data comes only from Claude Code's statusline `rate_limits` (`five_hour`, `seven_day`: `used_percentage`, `resets_at`), available after the first response in a session.
- **Unverified:** whether cloud Claude Code sessions report `rate_limits` the same way local ones do. A spike settles this before the usage check is built.

## Approaches considered

| | Approach | Trade-off | Decision |
|---|---|---|---|
| A | Scheduled cloud runs at fixed times, no usage check | Simple, works today; blind to actual usage | Built first, as the base |
| B | A + usage check at the start of each run | What Rohan described; depends on the spike | **Chosen** (A first, then add the check) |
| C | Always-on watcher polling usage via login token | Breaks Anthropic's terms | Rejected |

## Design

### The backlog = GitHub Issues
- Lives as issues on each of Rohan's repos (adding one from the GitHub phone app works).
- Labels:
  - `backlog`: eligible for the runner
  - `safe`: may run with no approval
  - `ask-first`: needs approval (below)
  - `approved`: Rohan's approval for an `ask-first` issue
  - `runner:done` / `runner:failed`: set by the runner
- Research/writing tasks: issues on a dedicated `backlog-notes` repo; the output is a markdown doc committed to a branch there and linked in the issue comment.

### Approval — *Claude's call, please check*
Rohan asked that it *ask him* when there's usage left. A cloud run can't reliably sit and wait for a reply, so approval is asynchronous:
- Adding the `approved` label to an `ask-first` issue (any time, from the phone) lets the next run pick it up.
- **Night mode:** labelling a `tonight` tracking issue (or commenting "tonight: go") pre-approves all `ask-first` tasks for that one night.
- With no approval, only `safe` tasks run — Rohan's rule.
- When a daytime run finds spare usage but only `ask-first` work, it sends a push notification ("~X% left before reset, N tasks waiting for approval") so he can label from his phone.

### Schedule
- Daytime: a couple of runs during office hours (e.g. 13:00 and 16:30 IST).
- Night: 01:00, 03:00, 05:00 IST.
- All times configurable.

### Each run (the skill's procedure)
1. **Check usage.** Read `rate_limits`. Continue only if both floors hold (defaults, configurable):
   - 7-day used < 80% — rising to 95% when the weekly reset is under 24 h away (that capacity would be lost anyway).
   - 5-hour used < 85%.
   - If `rate_limits` is unavailable: run at most `fallback_max_tasks` (default 1) and say so in the summary.
2. **Collect tasks.** Open issues labelled `backlog` and (`safe`, or `ask-first` + `approved`/tonight-mode), across configured repos, oldest first (or by a `priority:n` label if present).
3. **Work one task at a time.**
   - Code: new branch `backlog/<issue#>-<slug>`, make the change, run existing tests if any, push, open a **draft PR** linked to the issue.
   - Research/writing: write the doc in `backlog-notes`, push a branch, link it.
   - Comment on the issue with what was done; label `runner:done` or `runner:failed` + reason.
   - Re-check usage before starting the next task.
4. **Stop** when a floor is hit, the list is empty, or a per-run task cap (default 3) is reached.
5. **Summary.** One push notification + one comment on a `runner-log` issue: tasks done (links), failed, skipped-awaiting-approval, usage before/after.

### Hard limits (never unattended)
Merge · push to `main` / default branch · close or delete issues · change repo settings · force-push · touch secrets.

### Git identity
Commits authored as Rohan (his name/email). No `Co-Authored-By` or session attribution lines.

### Packaging
```
claude-backlog-runner/
  SKILL.md          # when to use, the run procedure above, hard limits
  config.example.yml  # repos, label names, floors, task caps, schedule
  scripts/
    read_usage.sh   # statusline hook → writes rate_limits to a file the skill reads
```
Each scheduled task's prompt is simply: "Run the claude-backlog-runner skill."

## Build order

1. **Spike (throwaway):** in a cloud Claude Code session, confirm `rate_limits` shows up via the statusline hook.
2. **v1 = Approach A:** skill + labels + scheduled runs + summary, using the fallback task cap.
3. **v1.1 = B:** turn on the usage floors once the spike confirms the data.

## Left to the builder

- Exact SKILL.md wording and config schema.
- Issue-ordering tie-breaks; how "run existing tests" is detected per repo (Godot vs Node vs Python).
- Summary formatting.
