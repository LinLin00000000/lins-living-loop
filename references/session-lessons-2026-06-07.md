# Session lessons: LLL design and skill creation

Use this note when refining or applying LLL for this user.

## Corrections from the design session

- `delegate_task` is synchronous. It is useful for short/medium parallel reasoning inside the parent turn, but it is not a durable/background worker. If the parent task is interrupted, child work may be cancelled.
- If work must outlive the current turn, choose a durable carrier: background terminal process, independent agent CLI process, cron/scheduler, a thin LLL runner, or Kanban.
- Do not frame this as “delegate_task is unreliable.” It is designed for a different lifetime.
- Codex is already the user's default coding agent. Do not spend LLL research effort comparing coding agents unless explicitly asked.
- LangGraph and similar frameworks may be worth studying separately, but they should not be part of default LLL because the complexity cost is too high.
- Kanban is an upgrade path for long-lived multi-profile projects, not the default LLL entry point.
- LLL should not depend on planning-with-files. It should own its own workdir, queue, checkpoints, logs, recovery state, and validation.

## Preferred decision frame

The user wants the highest complexity-performance ratio, not maximum automation. Default to:

1. File-backed LLL workdir.
2. Thin durable queue/checkpoint runner if task count/retries matter.
3. Existing carriers: current agent, synchronous subagent, terminal background, independent agent CLI, Codex, scripts, cron.
4. Kanban only when the work becomes a long-term multi-profile project.

Good phrasing:

> LLL is not a big framework. It is a portable file-backed supervisor/worker protocol with optional carrier adapters.

## Skill-build pitfall found and fixed

The first version of `scripts/dop.py init` overwrote existing `mission.md` and the layout-specific `recovery_state.md`. That violates LLL's durable recovery principle.

Correct behavior:

- `init` refuses to reinitialize an existing LLL workdir unless `--force` is explicit.
- `--force` backs up overwritten core files first.
- Task output paths must stay inside the LLL workdir, preferably under `internal/agents/<task-id>/` for new v2 workdirs, `collab/agents/<task-id>/` for transitional v1 workdirs, or legacy `agents/<task-id>/` for old root-layout workdirs.

This is a general LLL design rule: initialization should be conservative and should never silently destroy recovery state.
