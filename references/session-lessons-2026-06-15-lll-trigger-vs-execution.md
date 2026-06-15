# Session lesson: LLL trigger vs LLL execution

Use this reference when a task loads or mentions LLL but the actual work risks falling back to ordinary ad-hoc repo editing.

## User correction

The user pointed out that a long LLL skill-editing task loaded the LLL skill but did not actually use an LLL workdir. This violated the user's standing preference: for non-trivial tasks, default to LLL Lite and upgrade only when needed.

## Durable lesson

Loading `lins-living-loop` with `skill_view` is not the same as using LLL.

For non-trivial skill/repo/workflow edits, the minimum honest use is usually LLL Lite:

- create a small workdir;
- write `mission.md` and optional `notes.md`;
- record validation evidence under `internal/validation-report.md` or JSONL audit files when useful;
- keep final user-facing changes in the real project/repo, not necessarily inside the LLL workdir;
- link or summarize the validation in the final response.

This keeps the workflow durable without adding fake workers or ceremony.

## Trigger checklist

When a task is more than a tiny edit, ask before starting:

1. Will I touch several files, docs, templates, scripts, or references?
2. Will I run validation, smoke tests, or git commit/push?
3. Did the user ask to optimize/change a workflow or skill?
4. Could the task outlive a single simple tool call or need recovery?
5. Is the user likely to ask “why did you do it this way?” or “continue from that run?”

If yes to any meaningful combination, use at least LLL Lite. Do not substitute a chat `todo` list for file-backed state.

## Pitfall

When editing LLL itself, it can feel awkward to use the protocol being changed. Do not skip it for that reason. Use the simplest stable subset: `mission.md`, `notes.md`, validation evidence, and JSONL audit entries if relevant.


## Context drift contract

Large conversations (for example 100K+ context, many tool results, or a compaction boundary) are exactly where LLL earns its keep. The risk is not only losing text; it is semantic drift: the agent keeps acting from stale or half-remembered goals, constraints, validation criteria, and decisions.

For these tasks, create or refresh the file-backed contract before continuing substantive work:

- `mission.md`: current objective, constraints, success criteria, scope changes, and non-goals;
- `notes.md` or a root deliverable: compact reasoning/decisions that matter to the user;
- `internal/recovery-state.md`: current phase, last safe checkpoint, next action, blockers;
- `internal/validation-report.md` and JSONL audit files: what was actually checked and what changed.

Keep this lightweight. The goal is not ceremony; it is preventing hidden chat state from becoming the only source of truth.
