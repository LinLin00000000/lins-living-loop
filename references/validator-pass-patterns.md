# Validator pass patterns

Use this reference for independent validation of a LLL workspace.

## Validator stance

A validator is not the producer. It should read compact state first, check the result against the mission, and write a clear PASS / PASS_WITH_NOTES / FAIL verdict.

For current workdirs, use root deliverables plus `internal/` state. For transitional/legacy workdirs, use their equivalent `readable/`, `deliverables/`, `collab/`, or root state without migrating unless asked.

## Validation checklist

1. Recover from files, not chat: read `mission.md`, layout-specific queue/registry/recovery files, root numbered deliverables, relevant worker handoffs/artifacts, and the validator task file.
2. Run baseline structure validation when the helper exists, but label it correctly as baseline unless strict checks are implemented.
3. Independently verify important environment/tool claims with safe commands, avoiding secret file contents.
4. Check final deliverables for obvious secret leakage when the task involved config/auth/environment inspection. Prefer pattern scans over printing sensitive matches.
5. Validate mission criteria section by section, and separate PASS reasons from notes.
6. For current workdirs, check that root deliverables exist when needed, `internal/error-report.jsonl` and `internal/traceability.jsonl` parse, and no obsolete `output/`/index/standalone-next-step layer was generated.
7. Confirm that current next steps, if useful, are inside the primary report or relevant deliverable.
8. State the independence limit honestly: same-runtime second pass, separate worker/runtime, cross-model review, or human review.
9. Use `PASS_WITH_NOTES` rather than `PASS` when deliverables satisfy the mission but there is non-blocking shared-state drift, weaker-than-ideal independence, or evidence organization limitations.

## Verdict shape

```text
verdict: PASS|PASS_WITH_NOTES|FAIL
validated_at: <timestamp>
validator: <agent/tool>
```

Include:
- checked files;
- structure result;
- mission criteria result;
- blocking issues;
- non-blocking notes;
- recommended follow-up if any.
