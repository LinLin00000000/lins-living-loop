# LLL workdir UX migration checklist

Use this reference when changing LLL's own workdir layout, templates, helper scripts, or human-readable output conventions.

## Durable UX rule

A LLL workdir should be easy for two readers at once:

- Humans start from `output/00-index.md` and numbered `output/` files.
- Agents, runners, and supervisors use `internal/` for queues, logs, registry, recovery, validation, task state, raw inputs, and worker artifacts.
- Root stays shallow: normally only `mission.md`, `internal/`, and `output/`.

Do not make humans hunt through workflow machinery to find conclusions. Do not make agents infer state from final reports.

## Patch checklist

When modifying LLL layout or output conventions, update all layers together:

1. `SKILL.md`: canonical protocol, invariants, validation expectations, final response shape.
2. `scripts/lll.py` / compatibility `scripts/dop.py`: helper defaults, path helpers, generated `task.md`, `checkpoint`, `validate`, CLI help, and legacy compatibility.
3. `templates/workdir/`: mission, recovery, handoff, validation report, registry, index/error/trace/next-step expectations.
4. `templates/task/`: worker output contract, shared-state boundaries, logging, handoff format.
5. `templates/prompts/`: worker, synthesis worker, validation worker contracts.
6. `references/`: runner, observability/recovery, validator patterns, adapters, and any historical lessons that mention old paths.
7. Current LLL dogfood workspace: make the run itself demonstrate the intended layout when practical.

A doc-only patch is not enough when helper scripts or templates can still generate the old experience.

## Link policy verification

Verify that generated and templated Markdown uses stable links:

- Relative links for files generated inside the same LLL workdir.
- URLs or absolute paths for stable external resources.
- Plain text for temporary external/user-mentioned files likely to move.
- Numbered `output/NN-*.md` files for human-facing outputs.
- `output/00-index.md` mentions every file in `output/`.
- `output/90-error-report.md` and `output/91-traceability.md` are append-only audit files.
- `output/99-next-steps.md` is mutable and reflects the current next action.
- Worker task files should link to `mission.md`, `handoff.md`, `artifacts/`, `log.txt`, shared state, and assigned human-facing output areas where paths are stable.

## Reuse output file policy

Use the mixed strategy for human deliverables:

- Update the current `01-*` primary deliverable for same-scope corrections or small supplements.
- Create the next numbered output file (`02-*.md`, `03-*.md`, etc.) for independent follow-up analysis, design decision, new task result, or phase conclusion.
- Keep `00-index.md` current and make it obvious which file is the current recommended reading entry.
- Keep `90-error-report.md` for workflow/runtime errors only; user requirements and decisions belong in mission addenda, traceability, or numbered deliverables.

## Legacy compatibility rule

Keep old workdirs resumable.

- Canonical v2: `mission.md`, `internal/`, `output/`.
- Transitional v1: `mission.md`, `collab/`, `readable/`, plus root recovery/handoff/validation files.
- Legacy v0: root-level `tasks.jsonl`, `runs.jsonl`, `agent-registry.md`, `agents/`, or `deliverables/`.

Helpers should continue to read/write the detected old layout unless the user explicitly asks to migrate. New workdirs should not silently create an old layout just because legacy support exists.

## Verification checklist

Run at least:

- `python3 -m py_compile scripts/lll.py scripts/dop.py`
- `python3 scripts/lll.py --help` plus changed subcommand `--help`
- New-layout smoke test: `init`, `add-task`, `event`, `checkpoint`, `validate`, and inspect root entries plus task `out`.
- Transitional-layout smoke test if compatibility changed: construct minimal `collab/` + `readable/` files, then `validate`, `add-task`, `event`, `checkpoint`, `validate`.
- Legacy-layout smoke test: construct minimal old-style files, then `validate`, `add-task`, `event`, `checkpoint`, `validate`.
- Search for stale old-layout terms; keep only explicit transitional/legacy-compatibility mentions.
- If security/config/auth files are touched, scan for secret-like literals without printing matched values.

## Common pitfall

Exact multi-line patches against generated long Python strings are brittle. If a patch fails because the old string is not unique or not found, inspect the local block and replace a bounded line range or use smaller targeted patches. Do not repeat the same failed patch unchanged.
