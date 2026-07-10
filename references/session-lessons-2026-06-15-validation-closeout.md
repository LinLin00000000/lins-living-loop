# Session lesson: validator-only closeout repair loop

Use this when an independent validator must not edit shared state.

1. The validator writes detailed reasoning inside its own worker artifact and returns `PASS`, `PASS_WITH_NOTES`, or `FAIL` in the task-local handoff/status.
2. The single-writer supervisor consumes that verdict and performs closeout:
   - repair safe structural gaps;
   - update the validation task/status;
   - record the canonical verdict with `lll validation set` in `internal/validation.json`;
   - refresh `mission.md` and `internal/recovery.json`;
   - append trace/error JSONL entries when useful;
   - check human-facing deliverable language.
3. Run `lll closeout <workdir> --json --write-report` after shared state converges.
4. Do not deliver while validation is pending, a blocking finding remains, expected worker records are missing, or a primary deliverable is in the wrong language.

Registry views are derived from `tasks.jsonl` and worker `status.json`; do not maintain a duplicate supervisor registry or handoff file.
