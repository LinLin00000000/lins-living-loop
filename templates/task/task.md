# LLL Worker Task

```text
task_id: <T001>
carrier: <current|synchronous_subagent|foreground_command|background_process|agent_cli|code_agent|scheduler|durable_board>
preset: <default|fast-research|deep-research|critic|code|code-heavy|script>
status: pending
```

## Objective
<One narrow goal.>

## Inputs
- <path/source>

## Required outputs
- internal/agents/<task-id>/handoff.md
- internal/agents/<task-id>/artifacts/<file>

## Boundaries
- Do not edit shared final deliverables unless assigned.
- Do not edit shared state files (`internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/agent_registry.md`, `internal/recovery_state.md`) unless explicitly assigned and protected by a lock/runner API.
- Do not rely on chat context not present in files.
- Do not exceed scope without recording the reason.
- Default to the user-specified output language or current interaction language for prose; treat this as a hidden default and do not add language metadata labels unless language is explicitly part of the task. Use English for code, JSON keys, commands, API names, filenames, external terms, or user-specified English output.
- If assigned a human-facing deliverable, write it under output/ with a two-digit numeric prefix and stable Markdown links.
- If you create or modify any output/ file, update or ask the supervisor to update output/00_index.md.

## Logging
Append commands, sources, decisions, failures, and retries to internal/agents/<task-id>/log.txt.

## Handoff contract
Return only:
- status
- output paths
- 1-3 key results
- risks/blockers
- recommended next step
