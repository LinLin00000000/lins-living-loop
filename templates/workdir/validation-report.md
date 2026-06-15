# Validation Report

```text
verdict: pending
validated_at: <local-timezone ISO-8601/RFC3339>
validator: <agent/tool>
```

## Structure check
| criterion | status | evidence |
|---|---|---|
| required current-layout files exist | pending | [mission](../mission.md), [internal queue](tasks.jsonl), [traceability](traceability.jsonl), [error report](error-report.jsonl) |
| obsolete output layer absent | pending | no `output/`, `00-index.md`, or standalone next-step file generated for new workdirs |
| human-facing deliverables are top-level | pending | primary `../01-*` deliverable(s), when required by mission |
| JSONL audit logs parse | pending | [traceability](traceability.jsonl), [error report](error-report.jsonl), [runs](runs.jsonl) |
| human-facing output language is correct | pending | primary deliverable body follows requested/current interaction language |

## Mission criteria check
| criterion | status | evidence |
|---|---|---|
| <criterion> | pending | [<path/source>](<relative-or-stable-absolute-link>) |

## Blocking issues
- none yet

## Non-blocking notes
- none yet

## Traceability
Use `internal/traceability.jsonl` for append-only claim/source/change records. Link the relevant entries or summarize the checked item here.

## Final decision
pending
