# Output language and append-only discipline

Human-facing root deliverables are the user's reading surface. They should not silently fall back to English template prose, and they should not display language metadata as product noise.

## Output language rule

- Human-facing prose in root deliverables named from the task, such as `architecture-options.md` or `validation-summary.md` follows the user's explicitly requested output language.
- If the user did not specify an output language, use the current interaction language.
- Treat this as a hidden default. Do not add `language_rule`, `interaction_language`, or `output_language` markers to `mission.md` or deliverables merely to announce it.
- Record language only when it is a real task constraint: non-default output language, bilingual deliverables, translation work, or cross-language handoff risk. Put it in normal constraints/expected outputs/addenda, not in mandatory metadata fields.
- Keep filenames, JSON keys, commands, API names, code identifiers, and stable external proper nouns in English when useful for portability.
- Validate language explicitly before final delivery; do not rely on worker prompt language rules alone.

## Reuse deliverable lifecycle

On workspace reuse, choose the output file by semantic boundary:

- Update the primary root task-specific root deliverables deliverable for corrections, clarifications, style cleanup, small supplements, or rewrites of the same deliverable.
- Create root additional clearly named deliverables, etc. for independently readable analyses, decisions, new evidence packets, new task results, or new phase conclusions.
- Put current next steps inside the primary deliverable or relevant deliverable.
- Keep audit history in `internal/traceability.jsonl`; keep workflow/runtime failures in `internal/error-report.jsonl`; do not overload the primary deliverable as a transcript.

## Append-only timestamp rule

Append-only files preserve audit order and support workspace reuse. Every appended entry should carry a local-timezone ISO-8601/RFC3339 timestamp.

Applies to:

- `internal/error-report.jsonl`
- `internal/traceability.jsonl`
- `internal/runs.jsonl`
- `internal/logs/*.log`
- `internal/agents/<task-id>/log.txt`
- explicitly declared `internal/**/events.jsonl`, `journal.md`, or `history.md`

Good JSONL patterns:

```json
{"ts":"2026-06-08T13:12:00+08:00","type":"workflow_error","severity":"warning","what_happened":"...","evidence":["..."],"impact":"...","fix_or_fallback":"...","self_maintenance":"..."}
```

```json
{"ts":"2026-06-08T13:12:00+08:00","type":"claim","item":"...","evidence":["relative/path"],"status":"supported","notes":"..."}
```

## Internal append-only token-cost rule

On resume:

1. Read compact current-state files first: `mission.md`, `internal/recovery-state.md`, `internal/tasks.jsonl`, `internal/agent-registry.md`, task-local `status.json`, and task-local `handoff.md`.
2. Read append-only history only by tail, task id, time window, or entries since the last checkpoint.
3. If a log becomes important but large, create/update a compact snapshot or handoff instead of forcing future agents to ingest the full history.

## Mission as current contract

`mission.md` should be maintained during reuse. It is a compact current contract plus short timestamped addenda, not a frozen kickoff note and not a full transcript. Keep `updated_at`, `status`, success criteria, expected outputs, and recent scope changes current. Mark `status: completed` after final validation/delivery; if work resumes, set it back to `active` and append a timestamped addendum.

## Timezone

Use the user's known timezone when available; otherwise use the runtime/system local timezone with an explicit offset. Avoid defaulting to UTC just because the programming API is convenient. In Python helpers, prefer `datetime.now().astimezone().isoformat(timespec="seconds")`; in shell, prefer `date --iso-8601=seconds`.

## Pitfall

Do not treat a SKILL.md policy as implemented until generator surfaces are checked too. For LLL layout/UX rules, synchronize at least `SKILL.md`, `scripts/lll.py`, templates, prompts, references, README, and smoke tests.
