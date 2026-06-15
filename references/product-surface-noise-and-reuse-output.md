# Product surface noise and reuse output

Use this reference when a LLL run is optimizing the workflow/product surface itself, or when a user corrects how `mission.md`, root deliverables, or error/trace records should behave.

## Hidden defaults vs visible deliverables

- Follow the user's explicitly requested language; if none is specified, use the current interaction language.
- Do **not** add product-noise fields such as `language_rule`, `interaction_language`, or `output_language` to `mission.md` or human-facing deliverables.
- Only mention language visibly when language itself is a task constraint, a deliverable requirement, or a source of ambiguity that must be resolved.

## Error report scope

`internal/error-report.jsonl` is for workflow/runtime abnormalities, not for restating the user's goals.

Good entries:
- failed command and repair;
- wrong internal assumption and fix;
- stale skill guidance and patch;
- validation failure and recovery;
- queue/registry drift.

Do **not** record normal user requirements, new goals, scope additions, or product decisions as errors. Put those in `mission.md` addenda, tasks, root deliverables, or `internal/traceability.jsonl`.

## Reuse deliverable lifecycle

Do not create a new file for every chat turn.

- Update the current root `01-*` primary deliverable for same-scope corrections, clarifications, style cleanup, small supplements, or rewrites.
- Create root `02-*`, `03-*`, etc. when the new work is an independently readable analysis, decision, phase result, or substantial add-on.
- Do not keep a separate index for small file sets; root filenames and the final chat response should make the entry point obvious.
- Do not force all history into `01-final-report.md`; it should carry the current main conclusion, not become a changelog.
- Current next steps belong inside the primary report or relevant deliverable.
