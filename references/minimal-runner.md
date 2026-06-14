# Minimal LLL runner design

LLL does not need a heavy orchestrator by default. A useful runner can stay tiny.

## File helper vs actual runner

`scripts/lll.py` is the main file helper (`scripts/lll.py` / compatibility `scripts/dop.py` remains a compatibility shim), not a durable runner, daemon, dispatcher, or smart agent. It makes the file protocol easy:

- initialize a workdir
- add tasks
- record events
- show status
- update task state
- checkpoint recovery state
- validate workdir structure

An actual runner is a stronger component. It claims tasks, starts carriers, heartbeats, records process/job ids, completes/fails tasks, retries, reclaims stale leases, and enforces single-writer updates. Do not imply the helper provides that lifecycle unless those features are implemented.

Use the helper for LLL-lite and manual supervision. Add an actual runner only when task count, retries, leases, or overlapping workers make manual state updates unreliable.

## Durable files

New LLL workdirs use the canonical v2 layout: root `mission.md`, process/agent state under `internal/`, and human-facing output under `output/`.

- `internal/tasks.jsonl`: current queue; safe to rewrite atomically
- `internal/runs.jsonl`: append-only event history
- `internal/recovery-state.md`: compact resume instructions
- `internal/handoff.md`: compact supervisor handoff for future recovery
- `internal/validation-report.md`: validation verdict and evidence
- `internal/inputs/`: raw/reference materials introduced during the run
- `internal/agents/<task-id>/status.json`: per-task current state
- `internal/agents/<task-id>/handoff.md`: worker handoff
- `output/00-index.md`: required index of every file in output/
- `output/90-error-report.md`: required append-only error/correction/self-maintenance report
- `output/91-traceability.md`: required append-only claim/source/change trace map
- `output/99-next-steps.md`: required mutable current next actions
- `output/01-<deliverable>.md`: numbered primary human-facing outputs as needed

Transitional workdirs may use `collab/` + `readable/` with root recovery/handoff/validation files. Older legacy workdirs may have `tasks.jsonl`, `runs.jsonl`, `agent-registry.md`, `agents/`, and `deliverables/` at the root. Resume them as-is, but create new workdirs with `internal/` and `output/`.

## Task schema

Recommended fields:

```json
{
  "id": "T001",
  "title": "Research options",
  "status": "pending",
  "priority": 10,
  "depends_on": [],
  "carrier": "agent_cli",
  "preset": "deep-research",
  "attempts": 0,
  "max_attempts": 2,
  "out": "internal/agents/T001/",
  "goal": "Find and compare options",
  "acceptance": ["findings written", "sources listed", "handoff written"],
  "inputs": ["mission.md"],
  "created_at": "<ISO-8601>",
  "updated_at": "<ISO-8601>",
  "claim_id": null,
  "lease_until": null,
  "error": null
}
```

## Event schema

```json
{
  "ts": "<ISO-8601>",
  "run_id": "R001",
  "task_id": "T001",
  "actor": "supervisor",
  "carrier": "agent_cli",
  "event": "started",
  "status": "ok",
  "message": "worker launched",
  "artifacts": ["internal/agents/T001/task.md"],
  "exit_code": null,
  "duration_ms": null
}
```

## Simple helper lifecycle

1. `init`: create v2 files and directories.
2. `add-task`: create queue item and task directory.
3. `status`: summarize queue counts and active/blocked tasks.
4. `event`: append an event.
5. `set-status`: update task state and per-task status file.
6. `checkpoint`: rewrite the layout-specific `recovery-state.md` with latest safe point.
7. `validate`: check required files, JSONL validity, safe task output paths, legal statuses, dependencies, per-task file presence, required output audit files, and output index coverage. It supports `--mode auto|full|lite`; `auto` stays conservative and treats any workdir with a layout-specific task queue as full validation, full mode keeps strict worker-tree checks, and lite mode accepts simple honest Lite workspaces without fake worker directories.

`validate` is structure validation. It does not prove the mission is complete, claims are correct, tests passed, or deliverables are useful. Mission validation remains a separate independent LLL step.

## Lease and reclaim, only if needed

For most LLL-lite work, leases are unnecessary. Add leases when multiple workers or long background jobs may overlap.

A lease is just:

- `claim_id`: who owns the task now
- `lease_until`: time after which a supervisor may inspect/reclaim
- heartbeat events in `internal/runs.jsonl`

Reclaim only after checking the worker log/process when possible.

## Atomic update and single-writer rule

Shared LLL state has one writer at a time.

- In manual LLL-lite, the supervisor owns `internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/agent-registry.md`, and `internal/recovery-state.md`.
- In runner mode, the runner owns those shared files or exposes a narrow API/lock for updates.
- Workers write only `internal/agents/<task-id>/` unless explicitly assigned a numbered shared human deliverable under `output/`.

When rewriting `internal/tasks.jsonl`:

1. read all lines
2. write a complete `internal/tasks.jsonl.tmp`
3. replace `internal/tasks.jsonl` atomically
4. append an event to `internal/runs.jsonl`

This keeps recovery simple after crashes.

## What not to build early

Do not start with:

- database
- queue server
- event bus
- custom agent protocol
- distributed locks
- complex daemon
- GUI dashboard

Add those only when plain files have become the bottleneck.

## Included helper

This skill includes `scripts/lll.py`, a small stdlib helper. `scripts/lll.py` / compatibility `scripts/dop.py` remains as an old-name compatibility shim with the lifecycle commands above. It is optional; agents can also manage the files directly.

## Helper quickstart

```bash
python3 scripts/lll.py init ~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case --objective "<objective>"
python3 scripts/lll.py add-task <lll-workdir> --id T001 --title "<short title>" --goal "<worker goal>" --carrier agent_cli --preset deep-research
python3 scripts/lll.py add-task <lll-workdir> --id T002 --title "<dependent task>" --goal "<worker goal>" --depends-on T001
python3 scripts/lll.py status <lll-workdir> --all
python3 scripts/lll.py validate <lll-workdir>
python3 scripts/lll.py validate <lll-workdir> --mode lite   # explicit Lite validation
python3 scripts/lll.py validate <lll-workdir> --mode full   # strict worker-tree validation
```

The helper is intentionally conservative: it refuses to reinitialize an existing workdir unless `--force` is explicit, and task output paths must stay under `internal/agents/<task-id>/` for new v2 workdirs, `collab/agents/<task-id>/` for transitional v1 workdirs, or legacy `agents/<task-id>/` when resuming old root-layout workdirs.

`add-task --depends-on` is repeatable and also accepts comma-separated lists for convenience, for example `--depends-on T001 --depends-on T002` or `--depends-on T001,T002`. After using helper scripts to add tasks or dependencies, inspect `internal/tasks.jsonl` before launching workers so queue ids, dependencies, and output paths match the intended task graph.

## Strict structure validation checklist

For higher confidence, validate at least:

- required core files exist: `mission.md`, `internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/agent-registry.md`, `internal/recovery-state.md`, `internal/handoff.md`, `internal/validation-report.md`;
- `internal/tasks.jsonl` and `internal/runs.jsonl` parse as JSONL;
- task ids are unique and non-empty;
- task statuses are one of `pending`, `ready`, `in_progress`, `blocked`, `done`, `failed`, `cancelled`;
- dependencies point to existing task ids;
- every task `out` is relative, cannot escape the workdir, and resolves under `internal/agents/<task-id>/` for v2, `collab/agents/<task-id>/` for v1, or legacy `agents/<task-id>/` for old workdirs;
- every task directory has `task.md`, `status.json`, `log.txt`, `handoff.md`, and `artifacts/`;
- task-local `status.json` agrees with the queue where practical;
- `internal/agent-registry.md` mentions every worker/task expected to exist;
- `output/00-index.md` exists and mentions every file in `output/`;
- `output/90-error-report.md`, `output/91-traceability.md`, and `output/99-next-steps.md` exist;
- validation and internal handoff files exist before final delivery.

Even strict structure validation is not mission validation. It only says the recovery surface is coherent enough to inspect.


## Append-only files and token-cost control

Append-only files are useful for auditability but dangerous for context cost if every resume reads them in full.

Treat these as append-only by design:

- `internal/runs.jsonl`: event stream
- `internal/logs/supervisor.log` and `internal/logs/runner.log`: supervisor/runner logs
- `internal/agents/<task-id>/log.txt`: task-local command/source/error log
- optional `internal/**/events.jsonl`, `journal.md`, `history.md`: only if explicitly declared append-only

Resume order should prefer compact state first: `mission.md`, `internal/recovery-state.md`, `internal/tasks.jsonl`, `internal/agent-registry.md`, task-local `status.json`, and `handoff.md`. Then read append-only files only by tail, by task id, or by entries since the last checkpoint. If a log becomes important but large, write or refresh a compact handoff/snapshot instead of making future agents ingest the whole history.

Every append-only entry should include a local-timezone ISO-8601/RFC3339 timestamp so later agents can read “since checkpoint” slices.
