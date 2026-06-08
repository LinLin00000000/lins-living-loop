# LLL-lite vs PWF and default workdir

Session-derived workflow note.

Context:
- The user is moving from PWF-heavy planning toward LLL-lite as the default durable workflow for complex tasks.
- Old user preferences may still mention `planning-with-files-zh` and `~/hermes-pwf-record/`; do not let that legacy preference override an explicit request to use LLL.

Workdir rule:
- When the user asks to use LLL and does not provide a project-specific workdir, create the LLL run under `~/lll-work/`.
- Use a timestamped, short slug directory such as `~/lll-work/YYYYMMDD_HHMMSS_short-task-name/`: `_` separates date/time and timestamp/slug; avoid `YYYYMMDD-HHMMSS` so new workdirs sort and scan consistently.
- Only use an existing project directory when the task clearly belongs there or the user specifies it.
- Treat `~/hermes-pwf-record/` as legacy PWF storage, not a LLL default.

LLL-lite defaulting:
- For medium-complexity tasks, LLL-lite replaces PWF's `task_plan.md` / `findings.md` / `progress.md` pattern as the default durable workflow.
- Minimal LLL-lite can be: root `mission.md`, `internal/tasks.jsonl`, `internal/recovery_state.md`, `internal/handoff.md`, and numbered `output/` files.
- Meaningful LLL-lite should still create `output/00_index.md`, `output/90_error_report.md`, `output/91_traceability.md`, and `output/99_next_steps.md`.
- Full LLL is appropriate for long-running, multi-worker, independently validated, or interruption-prone tasks.
- PWF is legacy: use it only for existing PWF project recovery or when the user explicitly asks for the PWF skill. Do not create new PWF workdirs for ordinary complex tasks.

Pitfall:
- If a task mixes LLL terminology with old PWF memory, follow the explicit current task request first. If the user says "use LLL", initialize LLL state in `~/lll-work/` and do not create a new `~/hermes-pwf-record/` run unless explicitly requested.
- A path to an old LLL workdir can be reference material rather than a reuse signal. Reuse requires explicit continuation/recovery intent or a same-task active addendum.
