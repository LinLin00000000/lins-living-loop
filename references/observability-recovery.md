# Observability and recovery

LLL observability should be useful, cheap to resume, and append-friendly.

## What to record

Event log (`internal/runs.jsonl` in current workdirs, transitional `collab/runs.jsonl`, or legacy `runs.jsonl`):
- state transitions and process/job metadata
- queue changes
- checkpoints
- validation events

Error log (`internal/error-report.jsonl`):
- workflow/runtime abnormalities
- failed assumptions
- worker failures
- tool/quoting/path issues
- validation failures that reveal workflow problems
- self-maintenance actions

Trace log (`internal/traceability.jsonl`):
- claims and evidence
- source additions/removals
- output changes
- validation evidence
- assumptions and superseded items

## Current-state vs history

Snapshots/current-state files may be rewritten to the current truth:
- `mission.md`
- `internal/recovery.json`
- `internal/tasks.jsonl`
- `internal/validation.json`
- `internal/agents/<task-id>/status.json`
- `internal/agents/<task-id>/handoff.md`
- root deliverables named from the task, such as `architecture-options.md` or `validation-summary.md`

Append-only history files preserve audit order:
- `internal/runs.jsonl`
- `internal/error-report.jsonl`
- `internal/traceability.jsonl`
- `internal/logs/*.log`
- `internal/agents/<task-id>/log.txt`
- explicitly named `internal/**/events.jsonl`, `journal.md`, or `history.md`

Every append-only entry should use a local-timezone ISO-8601/RFC3339 timestamp.

## Resume order

1. Read `mission.md`.
2. Read `internal/recovery.json`.
3. Inspect task/status summaries.
4. Read relevant worker handoffs.
5. Read root deliverables relevant to the question.
6. Read JSONL audit tails/slices only when needed.
7. Read raw artifacts/logs only after compact files identify which ones matter.

## Repair discipline

When structural drift or missing records are found, repair the smallest useful surface:
- update `mission.md` if the current contract is stale;
- reconcile task/status files and refresh recovery/validation through the CLI;
- append a repair event to `internal/runs.jsonl`;
- append workflow-relevant repairs to `internal/error-report.jsonl`;
- append evidence/change records to `internal/traceability.jsonl`;
- rerun structure validation.

Compatibility repair only restores auditability of the file protocol; it does not prove mission quality.

## Error report scope

Do not record normal user goals, newly added requirements, scope additions, or product/design decisions as errors. Put those in `mission.md` addenda, tasks, root deliverables, or `internal/traceability.jsonl`.

If no meaningful workflow errors occurred, the initial `type:init` JSONL object is enough. Do not write ceremonial Markdown error reports just to say nothing happened.
