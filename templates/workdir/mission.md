# LLL Mission

```text
mission_id: <YYYYMMDD_HHMMSS_slug-or-stable-id>
created_at: <local-timezone ISO-8601/RFC3339>
updated_at: <local-timezone ISO-8601/RFC3339>
status: initialized
```

## Objective
<What outcome should be achieved?>

## Success criteria
- <Observable criterion>
- <Required output path under output/>
- <Validation expectation under internal/validation_report.md>

## Non-goals
- <What should not be done in this run?>

## Constraints and permissions
- Filesystem writes: <allowed paths>
- Network/API use: <allowed/not allowed>
- Code execution/background processes: <allowed/not allowed>
- External services/accounts: <allowed/not allowed>
- Time/budget/context limits: <limits>

## Inputs
- <path/source>: <purpose; raw/reference materials should be copied or summarized under internal/inputs/ when durable>

## Expected outputs
- [output/00_index.md](output/00_index.md): human reading order and links; indexes every file in output/
- [output/01_<file>.md](output/01_<file>.md): primary numbered human-facing deliverable when needed
- [output/90_error_report.md](output/90_error_report.md): append-only workflow/runtime errors, corrections, and self-maintenance notes; says none if no such errors occurred
- [output/91_traceability.md](output/91_traceability.md): append-only claim/source/change trace map
- [output/99_next_steps.md](output/99_next_steps.md): mutable current next actions for the user

## Execution policy
- Keep supervisor context small.
- Workers may be current-agent actions, subagents, scripts, independent agent CLIs, scheduled jobs, board workers, or humans.
- Workers write detailed outputs under [internal/agents/<task-id>/](internal/agents/).
- Raw inputs, cloned repos, long logs, validation, handoff, and recovery state stay under [internal/](internal/).
- Workers return only short handoffs.
- Include a compact LLL contract in child-worker assignments; do not assume the worker loaded this skill.
- Record state changes in this file, [internal/tasks.jsonl](internal/tasks.jsonl), [internal/runs.jsonl](internal/runs.jsonl), and [internal/recovery_state.md](internal/recovery_state.md).
- Keep human-facing deliverables in [output/](output/) and number them with two-digit prefixes for sorting.
- Human-facing output body text follows the hidden default: the user-specified output language, or the current interaction language if none is specified. Do not add language metadata labels merely to announce the default; record language only when it is an explicit task constraint.
- Keep [output/00_index.md](output/00_index.md) current whenever output files are added, removed, or renamed.
- Keep [output/90_error_report.md](output/90_error_report.md) and [output/91_traceability.md](output/91_traceability.md) append-only with local-timezone timestamped entries.
- Rewrite [output/99_next_steps.md](output/99_next_steps.md) as the current recommended next action changes.
- Use Markdown links for stable internal/external sources: relative links for files inside this workdir, URLs/absolute paths for stable external resources, and plain text for temporary external files whose location may change.
- Give brief progress updates for long-running, multi-stage, background, or multi-worker phases.
- Validate before final delivery.

## Mission addenda

Append short timestamped entries when the user changes scope, constraints, output expectations, or reuse context. Keep detailed evidence in internal/ and audit files. If language is explicitly part of the task, record it as an ordinary constraint/addendum, not as a default metadata field.

| ts | change | impact |
|---|---|---|
| <local-timezone ISO-8601/RFC3339> | <what changed> | <mission/output/validation impact> |

## Recovery quick start
1. Read this file and check `updated_at`, `status`, and recent addenda.
2. Read [internal/recovery_state.md](internal/recovery_state.md).
3. Inspect [internal/tasks.jsonl](internal/tasks.jsonl) status counts.
4. Read relevant [internal/agents/<task-id>/handoff.md](internal/agents/) files.
5. Read [output/00_index.md](output/00_index.md) for human-facing outputs.
6. Continue from the latest safe checkpoint.
