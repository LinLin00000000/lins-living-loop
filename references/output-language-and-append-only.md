# Output language and append-only discipline

Session lesson: human-facing `output/` files are the user's reading surface. They should not silently fall back to English template prose, and they also should not display language metadata as product noise.

## Output language rule

- Human-facing prose in `output/` follows the user's explicitly requested output language.
- If the user did not specify an output language, use the current interaction language.
- Treat this as a hidden default. Do not add `language_rule`, `interaction_language`, or `output_language` markers to `mission.md` or `output/` files merely to announce it.
- Record language only when it is a real task constraint: non-default output language, bilingual deliverables, translation work, or cross-language handoff risk. Put it in normal constraints/expected outputs/addenda, not in mandatory metadata fields.
- Keep filenames, JSON keys, commands, API names, code identifiers, and stable external proper nouns in English when useful for portability.
- Validate language explicitly before final delivery; do not rely on worker prompt language rules alone, because helper-generated templates can still contain English defaults.

## Reuse deliverable lifecycle

On workspace reuse, choose the output file by semantic boundary:

- Update `01-final-report.md` / the primary `01-*` deliverable for corrections, clarifications, style cleanup, small supplements, or rewrites of the same deliverable.
- Create `02-*`, `03-*`, etc. for independently readable analyses, decisions, new evidence packets, new task results, or new phase conclusions.
- Keep `00-index.md` as the navigation layer that names the current recommended reading entry.
- Keep audit history in `91-traceability.md`; keep workflow/runtime failures in `90-error-report.md`; do not overload the final report as a transcript.

## Append-only timestamp rule

Append-only files preserve audit order and support workspace reuse. Every appended entry should carry a local-timezone ISO-8601/RFC3339 timestamp.

Applies to:

- `output/90-error-report.md`
- `output/91-traceability.md`
- `internal/runs.jsonl`
- `internal/logs/*.log`
- `internal/agents/<task-id>/log.txt`
- explicitly declared `internal/**/events.jsonl`, `journal.md`, or `history.md`

Good patterns:

```markdown
## E005 — short title

ts: 2026-06-08T13:12:00+08:00

- What happened: ...
- Evidence: ...
- Impact: ...
- Fix/fallback: ...
- Self-maintenance: ...
```

```markdown
| id | ts | claim/change/output | evidence | validation |
|---|---|---|---|---|
| TR-008 | 2026-06-08T13:12:00+08:00 | output body follows the user-specified output language/current interaction language without visible language metadata unless language is task scope | ... | PASS |
```

## Internal append-only token-cost rule

Internal history is useful, but full-log rereads are expensive and usually unnecessary. On resume:

1. Read compact current-state files first: `mission.md`, `internal/recovery-state.md`, `internal/tasks.jsonl`, `internal/agent-registry.md`, task-local `status.json`, and task-local `handoff.md`.
2. Read append-only history only by tail, task id, time window, or entries since the last checkpoint.
3. If a log becomes important but large, create/update a compact snapshot or handoff instead of forcing future agents to ingest the full history.

## Mission as current contract

`mission.md` should be maintained during reuse. It is a compact current contract plus short timestamped addenda, not a frozen kickoff note and not a full transcript. Keep `updated_at`, `status`, success criteria, expected outputs, and recent scope changes current. Mark `status: completed` after final validation/delivery; if work resumes, set it back to `active` and append a timestamped addendum. Do not add mandatory language metadata; if language is explicit scope, record it as a normal constraint or addendum.

## Timezone

Use the user's known timezone when available; otherwise use the runtime/system local timezone with an explicit offset (for example `+08:00`). Avoid defaulting to UTC just because the programming API is convenient. In Python helpers, prefer `datetime.now().astimezone().isoformat(timespec="seconds")`; in shell, prefer `date --iso-8601=seconds`.

## Pitfall

Do not treat a SKILL.md policy as implemented until the generator surfaces are checked too. For LLL layout/UX rules, synchronize at least:

- `SKILL.md`
- `scripts/lll.py` / compatibility `scripts/dop.py`
- `templates/workdir/*`
- `templates/prompts/*`
- relevant `references/*`
- `mission.md`
- the current workdir's `mission.md`, `output/00-index.md`, `90-error-report.md`, `91-traceability.md`, and `99-next-steps.md`
