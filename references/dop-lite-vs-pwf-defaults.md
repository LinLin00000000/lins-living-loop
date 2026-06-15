# LLL Lite vs PWF defaults

Use this when choosing whether a medium task needs no LLL, LLL Lite, or full LLL.

## Current default

- For medium-complexity tasks, LLL Lite replaces older PWF-style `task_plan.md` / `findings.md` / `progress.md` patterns as the default durable workflow.
- Minimal LLL Lite can be: root `mission.md`, optional `notes.md`, optional task-specific root deliverable, and `internal/validation-report.md` when checks are nontrivial.
- Meaningful LLL Lite should not create fake worker directories, `output/`, indexes, or standalone next-step files.
- Full LLL is appropriate for long-running, multi-worker, independently validated, or interruption-prone tasks.

## Decision rule

Use the smallest durable surface that keeps the work recoverable:

| Situation | Structure |
|---|---|
| Simple answer / tiny edit | no LLL |
| Single-track task, modest evidence, one producer | LLL Lite |
| Multi-track research/coding/validation, long-running, or context-heavy | full LLL |

## Lite shape

```text
<lll-workdir>/
  mission.md
  notes.md                 # optional compact working notes
  <task-specific-name>.md  # optional human-facing result named from the task
  internal/
    validation-report.md   # optional for nontrivial checks
    traceability.jsonl     # optional when claims need traceability
    error-report.jsonl     # optional unless a workflow/runtime issue occurs
```

Lite may omit queue/registry/worker trees when there were no real workers.
