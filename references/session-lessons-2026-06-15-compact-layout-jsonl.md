# Session lesson: compact root deliverables + JSONL audit logs

Use this reference when tuning LLL workdir UX, helper generation, validation shape, or migration away from older `output/`-based layouts.

## User correction

The user wanted LLL to be strong but cheaper to operate:

- remove the `output/` folder for new workdirs;
- put human-facing deliverables directly beside `mission.md` at the workdir root;
- move traceability and error reporting under `internal/`;
- remove `00-index.md` and standalone next-step files;
- avoid preserving historical layout-detection complexity in the new structure;
- keep only necessary structure in `mission.md` and a few reports;
- consider JSONL for traceability/error logs because they are append-only.

## Durable design decision

For new workdirs, use this compact split:

```text
<lll-workdir>/
  mission.md
  <task-specific-name>.md    # optional human-facing deliverable named from the task
  <another-topic>.md         # optional split only when content/theme justifies it
  notes.md                  # optional Lite notes
  internal/
    error-report.jsonl      # append-only workflow/runtime abnormalities and repairs
    traceability.jsonl      # append-only claim/source/change/evidence map
    ...process/worker/validation state...
```

Do **not** generate `output/`, `00-index.md`, `99-next-steps.md`, `Next Step.md`, or `Next Steps.md` for new workdirs.

## Why JSONL fits

`error-report` and `traceability` behave like event streams, not polished human reports:

- future agents can append one object without rereading the full file;
- validation is cheap: parse each non-empty line as JSON;
- logs can be tailed or filtered by time/task/type;
- the primary human report stays clean and does not become an audit transcript.

Recommended objects stay small and flexible:

```json
{"ts":"<local-timezone ISO-8601>","type":"workflow_error","severity":"warning","what_happened":"...","evidence":["path-or-command"],"impact":"...","fix_or_fallback":"...","self_maintenance":"..."}
```

```json
{"ts":"<local-timezone ISO-8601>","type":"claim|source|change|validation","item":"...","evidence":["relative/path","https://example.com"],"status":"supported|assumption|validated|superseded","notes":"..."}
```

## Implementation checklist

When applying this kind of layout change, update all generator surfaces together:

1. `SKILL.md` canonical layout and final response shape.
2. `scripts/lll.py` init/add-task/checkpoint/validate/help text.
3. `templates/workdir/`, `templates/task/`, and `templates/prompts/`.
4. README files and active references.
5. Delete obsolete templates rather than keeping deprecated scaffolding that future agents might copy.
6. Run a smoke test that initializes a workdir, adds a task, appends an event, checkpoints, validates, confirms no `output/` directory exists, and parses JSONL files.

## Pitfalls

- Do not create a separate index just because multiple files exist; for small file sets, the root listing plus final chat response is enough.
- Do not create a separate next-step file; place current next steps inside the primary deliverable or relevant deliverable.
- Do not rewrite dated historical lesson files just to remove old paths if they are clearly historical. Update only active guidance that a future agent might follow as current protocol.
