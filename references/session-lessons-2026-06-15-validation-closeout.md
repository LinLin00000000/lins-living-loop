# Session lesson: validation closeout repair loop (2026-06-15)

Context: A full LLL research run created worker outputs and a root report, then launched an independent validation subagent. The validator correctly wrote `internal/validation-report.md` and, because it was instructed not to edit shared state, left shared files untouched. It found two non-blocking structural gaps: missing supervisor-level `internal/handoff.md` and `T006-validation` still `pending` in `internal/tasks.jsonl`.

Reusable lesson:

1. Treat independent validation as an input to a final supervisor closeout step, not the final state mutation itself.
2. If the validator is forbidden to edit shared state, the supervisor must immediately:
   - read/consume the validation verdict;
   - repair any structural notes that are safe and non-controversial;
   - update validation task status and registry rows;
   - check the language of each human-facing root deliverable that the final reply will point to; if the user did not request English and the interaction is in another language, English template prose in a release summary/report is a workflow defect to repair before closing;
   - refresh `mission.md` status, `internal/recovery-state.md`, and `internal/handoff.md`;
   - append trace/error JSONL entries for validation verdict and any repaired workflow gap.
3. Do not deliver immediately after the validation subagent returns if its summary mentions pending shared-state updates or missing expected outputs.
4. Run a final lightweight structure check after closeout: required files exist, JSONL parses, no root `output/` directory in current layout, root deliverable exists, and validation verdict is reflected in shared state.

This is not a reason to let validators edit shared state by default; single-writer discipline is still useful. The key is that supervisor closeout is a separate required loop after validator-only work.
