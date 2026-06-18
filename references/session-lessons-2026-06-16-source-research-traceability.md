# Session lesson: source-research LLL traceability

When LLL is used for source-code or architecture research, do not leave traceability until closeout. A final report can be useful while the traceability log remains too sparse; that weakens recovery and independent validation.

## Pattern

1. After repositories or external docs are fetched, append `source` records for the fixed inputs: repo URL, commit SHA, docs URL, evidence snapshot path.
2. When worker handoffs land, append `claim` records for the major supported findings before synthesis begins.
3. During synthesis, keep citations in the root report, but also map the top-level conclusions to `internal/traceability.jsonl`.
4. Validation should check both the root report and traceability density. A `PASS_WITH_NOTES` for sparse traceability should be repaired when cheap before final delivery.

## Minimum for source-research runs

For a two-repository comparison, aim for at least:
- one `source` record per repository with URL + commit;
- one `source` record for any official docs page used;
- three to six `claim` records for the central architecture/context/decision conclusions;
- one `validation` record with the independent verdict.

This is not ceremony: it lets future supervisors resume from claims and evidence without re-reading every worker log or raw repository file.
