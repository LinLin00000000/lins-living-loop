# LLL observability and recovery

LLL treats interruption as normal. The question is not “will this fail?” but “can the next supervisor see what happened and continue?”

## What to log

Supervisor log:
- mission changes
- decomposition decisions
- carrier choices
- worker launches
- fallback decisions
- validation verdicts
- final delivery path

Worker log:
- commands run
- sources queried
- files read/written
- assumptions
- errors and retries
- checkpoints

Event log (`internal/runs.jsonl` in new v2 workdirs, transitional `collab/runs.jsonl`, or legacy `runs.jsonl` in old root-layout workdirs):
- state transitions and process/job metadata
- artifact paths
- exit codes and durations when known

Artifacts:
- raw search outputs
- reports
- test logs
- diffs
- screenshots
- benchmark data

## Log placement

Use local logs inside the LLL workdir:

```text
internal/logs/supervisor.log
internal/logs/runner.log
internal/agents/<task-id>/log.txt
internal/runs.jsonl
```

This keeps audit data portable with the task. If a central log store exists, mirror events there, but keep local logs as the source of recovery.

Raw/reference materials introduced during the work should live under `internal/inputs/`, a task's `artifacts/`, or another clearly named `internal/` subdirectory. Avoid placing raw repositories, source dumps, logs, or debugging files at the workdir root; the root should stay shallow and human-readable.

## Append-only classification

LLL has two kinds of durable files:

- Snapshots/current-state files: `mission.md`, `internal/recovery_state.md`, `internal/tasks.jsonl`, `internal/agent_registry.md`, `internal/agents/<task-id>/status.json`, `internal/agents/<task-id>/handoff.md`, `internal/validation_report.md`, and `output/99_next_steps.md`. These may be rewritten to the current truth.
- Append-only history files: `internal/runs.jsonl`, `internal/logs/*.log`, `internal/agents/<task-id>/log.txt`, `output/90_error_report.md`, `output/91_traceability.md`, and explicitly named `internal/**/events.jsonl`, `journal.md`, or `history.md`. These preserve audit order and should use local-timezone ISO-8601/RFC3339 timestamps for each entry.

For token economy, resume from snapshots first. Read append-only files by tail, task id, or entries since the last checkpoint; do not default to full-file reads unless the file is small or the task is an audit of the history itself.

## Recovery quick pass

After interruption:

1. Read `mission.md`.
2. Read the layout-specific recovery file: `internal/recovery_state.md` for v2, root `recovery_state.md` for transitional/legacy.
3. Validate the layout-specific queue/event JSONL parse.
4. Inspect queue summary: done, active, blocked, failed, pending.
5. Compare queue, registry, and task-local `status.json` for drift.
6. For active tasks, check process/job status if possible.
7. For done tasks, read only `handoff.md` first.
8. For failed tasks, read status + last log lines.
9. Read `output/00_index.md` (or transitional `readable/00_index.md`) for human-facing deliverables.
10. Update recovery state before continuing.

Do not reconstruct state from chat history unless files are missing.

## Repairing structural debt in resumed workdirs

If structure validation finds that an old/resumed workdir is missing required task files, do not silently fabricate history. First inspect the task's `task.md`, `status.json`, `handoff.md`, artifacts, and shared queue/registry evidence.

Then choose the smallest honest repair:

- If enough evidence exists, create a minimal retroactive file that says it is a recovery note, lists the evidence paths used, and labels unknown raw commands/logs as unavailable.
- If evidence is insufficient, mark the task/workdir as partial or blocked instead of forcing a clean validation.

Record the repair in the layout-specific event log, `output/90_error_report.md` (or transitional `readable/90_error_report.md` if resuming a v1 workdir), and recovery state, then re-run structure validation. This compatibility repair only restores auditability of the file protocol; it does not prove mission quality.

## Handling upstream API instability

Symptoms:
- timeouts
- partial tool output
- child agent cancellation
- model errors
- rate limits
- long-context degradation

Responses:
- shrink the next unit of work
- switch from synchronous subagent to background agent/script
- write prompt/output paths before launching
- add retries with backoff for scripts
- preserve partial results as artifacts
- validate key claims from files/sources
- avoid asking the main supervisor to carry raw context

## Three-failure rule

For the same task:

1. First failure: diagnose and repair.
2. Second failure: change method, carrier, or scope.
3. Third failure: mark blocked with evidence and continue independent tasks.

Do not loop silently.

## Validation as observability

Validation is not just quality assurance; it is an observability checkpoint. It confirms:

- what was produced
- what was not produced
- what evidence supports claims
- what risks remain
- whether the work can be resumed or delivered

A LLL task without validation is incomplete unless it is explicitly LLL-lite and trivial.

If validation is `FAIL`, do not present the task as complete. Write the failure into `internal/validation_report.md`, create concrete follow-up tasks or record an explicit blocker, update recovery state, and continue where possible. `PASS_WITH_NOTES` may be delivered only when caveats are clear and non-blocking.

## Error and lessons report

LLL should improve from its own failures. For meaningful LLL runs, especially those that modify skills or workflows, create `output/90_error_report.md` by default.

Record workflow/runtime abnormalities and their repair path:
- failed assumptions
- worker failures or cancellations
- adapter, quoting, path, API, or tool issues
- registry/queue/status drift
- validation failures and follow-up tasks
- user corrections only when they reveal a workflow violation or wrong internal assumption
- stale or missing skill guidance
- better verification methods discovered

Do not record normal user goals, newly added requirements, scope additions, or product/design decisions as errors. Put those in `mission.md` addenda, `internal/tasks.jsonl`, `output/91_traceability.md`, or a numbered deliverable. If no meaningful workflow errors occurred, keep the file and say that explicitly. Small issues can be fixed directly, but workflow-relevant corrections should still be logged. Put unresolved/optional user actions in `output/99_next_steps.md`.

After validation, decide whether to patch an existing skill, create a new skill after user confirmation, update durable memory for stable facts, or explicitly record that no self-maintenance action is needed.
