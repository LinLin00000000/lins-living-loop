# Session lesson — LLL validator directory shape and output index self-entry (2026-06-14)

## Trigger

A full LLL run used readable worker directories such as `internal/agents/T001-core-memory/` while `internal/tasks.jsonl` used task ids `T001`, `T002`, etc. The helper validation command:

```bash
python3 scripts/lll.py validate --mode full <workdir>
```

failed because full validation expects exact task-id directories:

```text
internal/agents/T001/
internal/agents/T002/
...
```

It also flagged that `output/00-index.md` did not mention itself.

## Durable lesson

When a v2 workdir has `internal/tasks.jsonl`, treat the task id as a filesystem contract, not just a display id.

- If queue id is `T001`, create `internal/agents/T001/` exactly.
- Put semantic names in `task.md`, `handoff.md`, artifact filenames, or registry descriptions, not in the worker directory name.
- Do not use suffixed worker dirs such as `T001-core-memory` unless the queue id is also exactly `T001-core-memory` and every validator/registry path agrees.
- `output/00-index.md` should include a row for itself as well as all other files under `output/`.

## Repair pattern

If this drift occurs:

1. Create canonical directories `internal/agents/<task-id>/artifacts/` for each queue id.
2. Copy or move existing `task.md`, `handoff.md`, and artifacts from semantic/suffixed dirs into the canonical dirs.
3. Add missing `status.json` and `log.txt` with honest repair notes; do not fabricate detailed history.
4. Add `internal/handoff.md` if missing.
5. Add an entry to `output/90-error-report.md` describing the structural repair.
6. Add the self-entry row to `output/00-index.md`.
7. Re-run full validation and only deliver after it passes or after an explicit blocker is recorded.

## Preferred preventive checklist

Before launching workers in full LLL:

- Write `internal/tasks.jsonl` first.
- Create `internal/agents/<exact-task-id>/` directories from the ids in the queue.
- Avoid semantic suffixes in directory names.
- Keep semantic labels in `agent-registry.md` and `task.md`.
- Run structure validation before final delivery, not after the final response draft.
