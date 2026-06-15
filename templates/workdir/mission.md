# LLL Mission

```text
mission_id: <YYYYMMDD-HHMMSS_short-description-in-kebab-case-or-stable-id>
created_at: <local-timezone ISO-8601/RFC3339>
updated_at: <local-timezone ISO-8601/RFC3339>
status: initialized
```

## Objective
<What outcome should be achieved?>

## Success criteria
- <Observable criterion>
- <Required root deliverable, e.g. `01-final-report.md`, when needed>
- <Validation expectation under `internal/validation-report.md`>

## Non-goals
- <What should not be done in this run?>

## Constraints and permissions
- Filesystem writes: <allowed paths>
- Network/API use: <allowed/not allowed>
- Code execution/background processes: <allowed/not allowed>
- External services/accounts: <allowed/not allowed>
- Time/budget/context limits: <limits>

## Inputs
- <path/source>: <purpose; raw/reference materials should be copied or summarized under `internal/inputs/` when durable>

## Expected outputs
- Root human-facing deliverable(s), usually `01-<file>.md`; merge when one file preserves thematic completeness, split when there are multiple independent themes or the file becomes too large.
- Current next steps are a section inside the primary report or relevant deliverable, not a standalone Next Steps file.
- `internal/error-report.jsonl`: append-only workflow/runtime abnormalities, repairs, and self-maintenance events.
- `internal/traceability.jsonl`: append-only claim/source/change trace entries.

## Execution policy
- Keep supervisor context small.
- Workers may be current-agent actions, subagents, scripts, independent agent CLIs, scheduled jobs, board workers, or humans.
- Workers write detailed outputs under [internal/agents/<task-id>/](internal/agents/) only when there are real worker contexts/background jobs/runner tasks.
- Raw inputs, cloned repos, long logs, validation, handoff, recovery state, traceability, and error logs stay under [internal/](internal/).
- Human-facing deliverables live at the workdir root beside this file; do not create `output/`, `00-index.md`, or standalone next-step files for new workdirs.
- Human-facing output body text follows the hidden default: the user-specified output language, or the current interaction language if none is specified. Do not add language metadata labels merely to announce the default.
- Record state changes in this file, [internal/tasks.jsonl](internal/tasks.jsonl), [internal/runs.jsonl](internal/runs.jsonl), and [internal/recovery-state.md](internal/recovery-state.md).
- Append JSONL objects to [internal/error-report.jsonl](internal/error-report.jsonl) and [internal/traceability.jsonl](internal/traceability.jsonl); do not reread/rewrite whole logs just to append.
- Use Markdown links for stable internal/external sources: relative links for files inside this workdir, URLs/absolute paths for stable external resources, and plain text for temporary external files whose location may change.
- Give brief progress updates for long-running, multi-stage, background, or multi-worker phases.
- Validate before final delivery.

## Mission addenda

Append short timestamped entries when the user changes scope, constraints, output expectations, or reuse context. Keep detailed evidence in `internal/` and audit JSONL files. If language is explicitly part of the task, record it as an ordinary constraint/addendum, not as a default metadata field.

| ts | change | impact |
|---|---|---|
| <local-timezone ISO-8601/RFC3339> | <what changed> | <mission/output/validation impact> |

## Recovery quick start
1. Read this file and check `updated_at`, `status`, and recent addenda.
2. Read [internal/recovery-state.md](internal/recovery-state.md).
3. Inspect [internal/tasks.jsonl](internal/tasks.jsonl) status counts when present.
4. Read relevant [internal/agents/<task-id>/handoff.md](internal/agents/) files when workers exist.
5. Read root deliverables such as `01-*.md`; inspect JSONL audit tails only as needed.
6. Continue from the latest safe checkpoint.
