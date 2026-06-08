# Product-surface noise, error semantics, and reused-output strategy

Use this reference when a LLL run is optimizing the workflow/product surface itself, or when a user corrects how `mission.md`, `output/`, or error reports should behave.

## Hidden defaults vs visible deliverables

- Treat interaction/output language as a hidden default, not visible metadata.
- Follow the user's explicitly requested language; if none is specified, use the current interaction language.
- Do **not** add product-noise fields such as `language_rule`, `interaction_language`, or `output_language` to `mission.md` or human-facing `output/*.md` files.
- Only mention language visibly when language itself is a task constraint, a deliverable requirement, or a source of ambiguity that must be resolved.

## Error Report scope

`output/90-error-report.md` is for workflow/runtime abnormalities, not for restating the user's goals.

Record:
- failed assumptions;
- worker/tool/template/helper/skill defects;
- validation failures;
- queue/registry/status drift;
- abnormal recovery steps;
- fixes applied and follow-up hardening items.

Do **not** record normal user requirements, new goals, scope additions, or product decisions as errors. Put those in `mission.md` addenda, `internal/tasks.jsonl`, `output/91-traceability.md`, or a numbered deliverable.

## Reused workspace output strategy

When a LLL workspace is reused:

- Update `01-*` when the new work is a small correction, clarification, refinement, or convergence of the same main deliverable.
- Create `02-*`, `03-*`, etc. when the new work is an independently readable analysis, decision, phase result, or substantial add-on.
- Keep `00-index.md` as the navigation layer. It should tell the reader which file is the current recommended entry point and what each numbered deliverable is for.
- Do not force all history into `01-final-report.md`; it should carry the current main conclusion, not become a changelog.

## Analyze-only guardrail

If the user says “先不要执行 / analyze first / don’t execute yet,” do not mutate the LLL workspace, templates, skill files, or outputs. Provide the decision analysis first, then wait for explicit approval before writing files or running workflow-changing commands.
