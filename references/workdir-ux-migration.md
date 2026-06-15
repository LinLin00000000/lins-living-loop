# LLL workdir UX migration checklist

Use this reference when changing LLL's own workdir layout, templates, helper scripts, or human-readable output conventions.

## Durable UX rule

A LLL workdir should be easy for two readers at once:

- Humans start from `mission.md` plus root deliverables named from the task, such as `architecture-options.md` or `validation-summary.md`.
- Agents, runners, and supervisors use `internal/` for queues, logs, registry, recovery, validation, task state, raw inputs, worker artifacts, traceability, and error records.
- Root stays shallow but useful: `mission.md`, a small number of human deliverables, optional `notes.md`, and `internal/`.

Do not make humans hunt through workflow machinery to find conclusions. Do not make agents infer state from final responses. Do not recreate `output/`/index layers unless the user explicitly asks for an old layout.

## Patch checklist

When modifying LLL layout or output conventions, update all layers together:

1. `SKILL.md`: canonical protocol, invariants, validation expectations, final response shape.
2. `scripts/lll.py` / compatibility `scripts/dop.py`: helper defaults, path helpers, generated `task.md`, `checkpoint`, `validate`, CLI help, and compatibility stance.
3. `templates/workdir/`: mission, recovery, handoff, validation report, registry, JSONL audit templates.
4. `templates/task/`: worker output contract, shared-state boundaries, logging, handoff format.
5. `templates/prompts/`: worker, synthesis worker, validation worker contracts.
6. `README*` and `references/`: runner, observability/recovery, validator patterns, adapters, and any current guidance that mentions old paths.
7. Current LLL dogfood workspace: make the run itself demonstrate the intended layout when practical.

A doc-only patch is not enough when helper scripts or templates can still generate the old experience.

## Link policy verification

Verify that generated and templated Markdown uses stable links:

- Relative links for files generated inside the same LLL workdir.
- URLs or absolute paths for stable external resources.
- Plain text for temporary external/user-mentioned files likely to move.
- Root Markdown files with task-specific names for human-facing deliverables.
- Next steps live inside the primary deliverable or relevant deliverable.
- `internal/error-report.jsonl` and `internal/traceability.jsonl` are append-only JSONL audit files.
- Worker task files link to `mission.md`, `handoff.md`, `artifacts/`, `log.txt`, shared state, and assigned human-facing output areas where paths are stable.

## Reuse output file policy

Use the mixed strategy for human deliverables:

- Update the current task-specific primary deliverable for same-scope corrections or small supplements.
- Create another clearly named root deliverable for independent follow-up analysis, design decision, new task result, or phase conclusion.
- Do not maintain a separate index for small file sets; a few root files should be readable directly from the directory listing.
- Keep workflow/runtime errors in `internal/error-report.jsonl`; user requirements and decisions belong in mission addenda, traceability, or root deliverables.

## Legacy compatibility rule

Keep old workdirs resumable, but do not carry their complexity into new workdirs.

- Current: `mission.md`, root deliverables, `internal/`.
- Transitional: `mission.md`, `collab/`, `readable/`, plus root recovery/handoff/validation files.
- Legacy: root-level `tasks.jsonl`, `runs.jsonl`, `agent-registry.md`, `agents/`, or `deliverables/`.

Helpers should detect old workdirs loosely enough to avoid destructive writes, but new helper/template output should not preserve redundant old-layout scaffolding.

## Verification checklist

Run at least:

- `python3 -m py_compile scripts/lll.py scripts/dop.py`
- `python3 scripts/lll.py --help` plus changed subcommand `--help`
- Current-layout smoke test: `init`, inspect root entries, `add-task`, `event`, `checkpoint`, `validate`, and confirm there is no generated `output/`.
- Legacy smoke only if compatibility code changed materially.
- Search for stale old-layout terms; keep only explicit transitional/legacy/historical mentions.
- If security/config/auth files are touched, scan for secret-like literals without printing matched values.

## Common pitfall

Exact multi-line patches against generated long Python strings are brittle. If a patch fails because the old string is not unique or not found, inspect the local block and replace a bounded line range or use smaller targeted patches. Do not repeat the same failed patch unchanged.
