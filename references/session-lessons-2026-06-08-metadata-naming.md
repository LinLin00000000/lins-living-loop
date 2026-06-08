# Session lesson: timestamp naming and visible metadata blocks

This note records a LLL self-maintenance pass from 2026-06-08. Use it when changing LLL workdir naming, helper-generated Markdown, or bundled templates.

## What changed

- New LLL workdirs should use `~/lll-work/YYYYMMDD_HHMMSS_slug/`; old `~/dop-work/` remains a compatibility root for historical DOP runs.
- Use `_` between date and time and another `_` before the slug.
- Avoid new defaults like `YYYYMMDD-HHMMSS_slug`; mixed timestamp separators are visually noisy and make directory listings harder to scan.
- Historical workdirs remain valid; do not bulk-rename old workdirs unless the user explicitly asks for a migration pass.

## Markdown metadata rendering lesson

Top-of-file metadata written as bare Markdown lines can render poorly in some clients, especially when multiple key/value lines are treated as one paragraph. For generated or templated LLL files, prefer a visible fenced metadata block:

```text
created_at: 2026-06-08T15:30:07+08:00
updated_at: 2026-06-08T15:30:07+08:00
status: initialized
```

Apply this to generated/templated files such as:

- `mission.md`
- `output/90_error_report.md`
- `output/91_traceability.md`
- `output/99_next_steps.md`
- `internal/recovery_state.md`
- `internal/validation_report.md`
- `internal/handoff.md`
- `internal/agents/<task-id>/task.md`
- `internal/agents/<task-id>/handoff.md`

## Verification pattern

When changing this surface, run a full helper/template smoke test rather than a doc-only patch:

1. `python3 -m py_compile scripts/lll.py scripts/dop.py`
2. `python3 scripts/lll.py --help`
3. v2 smoke: `init`, `add-task`, `event`, `checkpoint`, `validate`
4. Inspect the generated top sections and assert ` ```text ` appears near the top of metadata-bearing files.
5. Transitional v1 smoke: construct `collab/` + `readable/`, then `validate`, `checkpoint`, `validate`.
6. Legacy smoke: construct root `tasks.jsonl` + `deliverables/`, then `validate`, `checkpoint`, `validate`.
7. Search for stale `YYYYMMDD-HHMMSS` examples; remaining mentions should be explicit negative examples or historical compatibility notes.

## Pitfalls

- `output/00_index.md` must list itself as well as every other file in `output/`; final structure validation will catch this.
- If the skill directory is not a git repository, do not rely on `git diff` as evidence. Record changed files and smoke-test evidence in `output/91_traceability.md` / `internal/validation_report.md` instead.
- Broad file searches inside tool wrappers can produce oversized outputs. If a broad search fails, narrow the pattern or read bounded file sections; the durable lesson is the bounded-inspection pattern, not a permanent claim that the tool is broken.
