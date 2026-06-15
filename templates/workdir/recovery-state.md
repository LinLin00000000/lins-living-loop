# Recovery State

```text
status: initialized
last_updated: <local-timezone ISO-8601/RFC3339>
current_phase: setup
last_safe_checkpoint: workdir_created
active_tasks: none
blocked_tasks: none
running_processes: none
next_supervisor_action: define or run next task
```

## Resume steps
1. Read [mission.md](../mission.md).
2. Validate [internal/tasks.jsonl](tasks.jsonl) and [internal/runs.jsonl](runs.jsonl) when present.
3. Inspect task status summary.
4. Read only relevant worker handoffs under `internal/agents/<task-id>/handoff.md` first.
5. Read root deliverables such as `../01-*.md`; inspect `traceability.jsonl` / `error-report.jsonl` tails only as needed.
6. Continue from last_safe_checkpoint.
