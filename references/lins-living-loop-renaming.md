# Lin's Living Loop / LLL rename draft guidance

Use this reference when the user asks about renaming, rebranding, publicly packaging, or philosophically reframing LLL as `Lin's Living Loop` / `LLL`.

## Current user-approved direction

Treat `Lin's Living Loop` as a serious draft name, not as a joke or a branding problem to neutralize. The user's preference is that the personal mark (`Lin's`) is acceptable and even desirable; the center of gravity should be `Living` — living work, self-growth, repair, continuation, and iteration — rather than a cold protocol aesthetic.

Recommended public naming stack, pending explicit final approval:

```text
Lin's Living Loop / LLL
A tiny file-backed living loop for durable AI-agent work.
Formerly LLL — Lin's Living Loop.
```

## Workflow rule for rename/rebrand work

If the user asks for rename analysis, a theme migration plan, README wording, template changes, or GitHub packaging strategy but says not to modify the skill yet, do not patch the live skill. Create a fresh draft workspace instead. For LLL-specific drafts, prefer:

```text
~/lll-work/<timestamp>_<slug>/
```

Keep old `~/dop-work/` directories resumable and do not bulk-rename old workdirs unless the user explicitly asks for migration.

## Living design lens

`Living` should affect philosophy and product language, not turn the machine interface into a fantasy taxonomy.

Good balance:

- Public narrative: living loop, caretaker, habitat, growth, recovery, repair, lineage, next loop.
- Machine paths: keep clear names such as `mission.md`, root task-specific deliverables, `internal/`, `tasks.jsonl`, `runs.jsonl`, `error-report.jsonl`, `traceability.jsonl`, and `recovery-state.md`.
- Template headings may carry living language while filenames remain stable, e.g. `Validation Report — Health Check` or a `Next Loop` section inside the primary deliverable.

Avoid over-metaphorizing paths such as `seed.md`, `roots/`, `fruits/`, or `scars.md` as canonical names; they are charming but reduce portability and agent comprehension.

## Core sentence candidates

Preferred balanced version:

```text
The filesystem is where the work lives.
The chat is only the current interface.
The agent is the caretaker of the next loop.
```

More poetic version:

```text
The filesystem is where the work lives.
The chat is only the current weather.
The agent is the caretaker of the next loop.
```

More technical version:

```text
The filesystem is the durable body of the work.
The chat is a temporary control surface.
The agent is the current caretaker.
```

## Suggested lifecycle language

Use this as the LLL-facing loop:

```text
Seed → Split → Work → Trace → Heal → Validate → Hand off → Grow or Close
```

Mapping:

| LLL step | Existing LLL action |
|---|---|
| Seed | Write or update `mission.md` |
| Split | Decompose `tasks.jsonl` and worker `task.md` |
| Work | Workers write artifacts and logs |
| Trace | Append claims/evidence to `internal/traceability.jsonl` |
| Heal | Append workflow wounds and repairs to `internal/error-report.jsonl` |
| Validate | Write `internal/validation-report.md` |
| Hand off | Refresh `internal/handoff.md` and `internal/recovery-state.md` |
| Grow or Close | Put current next steps inside the primary deliverable or relevant root deliverable |

## Migration stance

For a future approved migration:

1. Start with wording and trigger compatibility: `LLL`, `Lin's Living Loop`, `LLL`, and `Lin's Living Loop` should all trigger the skill during transition.
2. Then update templates/headings and README.
3. Then change default new work root from `~/dop-work/` to `~/lll-work/`.
4. Only later rename helper scripts or directories, and provide compatibility shims such as `dop.py` → `lll.py`.

Do not mechanically search-and-replace `LLL`; some mentions must remain as legacy compatibility notes.
