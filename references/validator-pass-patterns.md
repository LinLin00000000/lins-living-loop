# Validator pass patterns

Session lesson: 2026-06-07 T012 independent validation of a LLL comprehensive report.

Use this when acting as a validation worker or when supervising one.

## Validator-only boundary

If the assigned task is independent validation, do not silently become the supervisor/runner. The validator may write under its own task area (`internal/agents/<task-id>/` in v2), especially:

- `artifacts/independent_validation.md`
- `handoff.md`
- task-local `status.json`
- `log.txt`

But it should not edit shared state files (`internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/agent_registry.md`, `internal/recovery_state.md`) unless the task explicitly grants runner/supervisor ownership. If shared-state drift is found, record it as a note and recommend supervisor reconciliation.

For transitional workdirs, use equivalent `collab/` paths. For legacy workdirs, use equivalent root queue/registry and `agents/<task-id>/` paths.

## Useful validation shape

1. Recover from files, not chat: read `mission.md`, layout-specific queue/registry/recovery files, numbered `output/` deliverables, relevant worker handoffs/artifacts, and the validator task file.
2. Run baseline structure validation when the helper exists, but label it correctly as baseline unless strict checks are implemented.
3. Independently verify important environment/tool claims with safe commands, avoiding secret file contents.
4. Check final deliverables for obvious secret leakage when the task involved config/auth/environment inspection. Prefer pattern scans over printing sensitive matches.
5. Validate mission criteria section by section, and separate PASS reasons from notes.
6. Check that `output/00_index.md` mentions every file in `output/`, required audit files exist, and `output/99_next_steps.md` reflects the current state.
7. State the independence limit honestly: same-runtime second pass, separate worker/runtime, cross-model review, or human review.
8. Use `PASS_WITH_NOTES` rather than `PASS` when deliverables satisfy the mission but there is non-blocking shared-state drift, weaker-than-ideal independence, or evidence organization limitations.

## Common PASS_WITH_NOTES causes

- `internal/agent_registry.md` or queue status lags behind worker handoffs/status, but the mission deliverable is sound.
- `dop.py validate` passes but is known to be baseline only.
- The validator is a separate pass in the same runtime rather than a different runtime/model.
- Some intermediate artifacts are thin, but final claims are independently rechecked.

## Handoff wording

Keep the validator handoff short:

- verdict;
- output paths;
- 2-4 key findings;
- notes/risks explaining why not pure PASS if applicable;
- recommended next supervisor action.
