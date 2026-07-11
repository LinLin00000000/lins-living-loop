# Minimal LLL runner design

LLL does not need a heavy orchestrator by default. A useful runner can stay tiny.

## File helper vs actual runner

`scripts/lll.py` is the main file helper; `scripts/dop.py` remains only as an old-name compatibility shim. The helper does not run agents. It makes the file protocol easy:

- initialize a workdir
- add tasks
- record events
- show status
- update task state
- checkpoint recovery state
- validate workdir structure

An actual runner is a stronger component. It claims tasks, starts carriers, heartbeats, records process/job ids, completes/fails tasks, retries, reclaims stale leases, and enforces single-writer updates. Do not imply the helper provides that lifecycle unless those features are implemented.

Use the helper for LLL Lite and manual supervision. Add an actual runner only when task count, retries, leases, or overlapping workers make manual state updates unreliable.

## Durable files

New LLL workdirs use the current compact layout: root `mission.md`, root human-facing deliverables, and process/agent/audit state under `internal/`.

- `mission.md`: current task contract
- `<task-specific-name>.md`, `<another-topic>.md`: optional root human-facing outputs named from the task as needed
- `notes.md`: optional Lite working notes
- `internal/tasks.jsonl`: current queue; safe to rewrite atomically
- `internal/runs.jsonl`: append-only event history
- `internal/error-report.jsonl`: append-only workflow/runtime abnormality and repair records
- `internal/traceability.jsonl`: append-only claim/source/change/evidence map
- `internal/recovery.json`: canonical current resume snapshot
- `internal/validation.json`: canonical current validation verdict and evidence pointers
- `internal/inputs/`: raw/reference materials introduced during the run
- `internal/agents/<task-id>/status.json`: per-task current state
- `internal/agents/<task-id>/handoff.md`: worker handoff

New helper output intentionally does not create `output/`, `00-index.md`, or standalone next-step files. Transitional/legacy workdirs may still contain `collab/`, `readable/`, `deliverables/`, or root-level state. Leave unrelated archives untouched; when a user explicitly continues one with LLL 0.2, discover it loosely, migrate its active machine state once to current JSON/JSONL placement, and never dual-write old and new state.

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

## Error/trace JSONL schemas

`internal/error-report.jsonl` example:

```json
{"ts":"<local-timezone ISO-8601>","type":"workflow_error","severity":"warning","what_happened":"...","evidence":["path-or-command"],"impact":"...","fix_or_fallback":"...","self_maintenance":"..."}
```

`internal/traceability.jsonl` example:

```json
{"ts":"<local-timezone ISO-8601>","type":"claim|source|change|validation","item":"...","evidence":["relative/path","https://example.com"],"status":"supported|assumption|validated|superseded","notes":"..."}
```

## Simple helper lifecycle

1. `init`: create current-layout files and directories.
2. `add-task`: create queue item and task directory, then refresh the compact queue discoverability summary in `recovery.json` under the same queue lock.
3. `status`: project queue records/counts plus current recovery/validation snapshots as one JSON response; it does not store a new truth.
4. `event`: append an event.
5. `set-status`: update task state and per-task status file.
6. `checkpoint`: atomically update `internal/recovery.json` while preserving extension fields.
7. `validation set/show`: atomically update or read `internal/validation.json`.
8. `validate`: check required files, JSON/JSONL validity, safe task output paths, legal statuses, dependencies, per-task file presence, and absence of obsolete current-layout output surface. It supports `--mode auto|full|lite`.

`validate` is structure validation. It does not prove the mission is complete, claims are correct, tests passed, or deliverables are useful. Mission validation remains separate.

## Lease and reclaim, only if needed

For most LLL Lite work, leases are unnecessary. Add leases when multiple workers or long background jobs may overlap.

A lease is just:

- `claim_id`: who owns the task now
- `lease_until`: time after which a supervisor may inspect/reclaim
- heartbeat events in `internal/runs.jsonl`

Reclaim only after checking the worker log/process when possible.

## Atomic update and single-writer rule

Shared LLL state has one writer at a time.

- In manual LLL Lite, the supervisor owns `internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/recovery.json`, and `internal/validation.json`.
- In runner mode, the runner owns those shared files or exposes a narrow API/lock for updates.
- Workers write only `internal/agents/<task-id>/` unless explicitly assigned a root human deliverable.

When rewriting `internal/tasks.jsonl`:

1. read all lines
2. write a complete `internal/tasks.jsonl.tmp`
3. replace `internal/tasks.jsonl` atomically
4. refresh `recovery.json.operational_queue` (paths, observation watermark, nonterminal count) while retaining `tasks.jsonl` as the owner
5. append an event to `internal/runs.jsonl`

This keeps recovery simple after crashes.

The reference CLI waits up to a small bounded interval (currently 5 seconds) when another supported queue mutation holds `tasks.lock`. This absorbs ordinary short CLI overlap without forcing every caller to implement retries. Timeout remains an explicit failure, stale-lock reclamation still uses the lock TTL, and this mechanism does not claim to serialize independent workers outside queue mutation or implement the stronger Worksite-wide primary-writer lease. If owner metadata is missing or malformed, the lock-directory modification time becomes the conservative TTL fallback instead of causing immediate deletion or a permanently unreclaimable orphan; failure while publishing new owner metadata cleans up the just-created lock.

## What not to build early

Do not start with a database, queue server, event bus, custom agent protocol, distributed locks, complex daemon, or GUI dashboard. Add those only when plain files have become the bottleneck.

## Helper quickstart

```bash
python3 scripts/lll.py init ~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case --objective "<objective>"
python3 scripts/lll.py add-task <lll-workdir> --id T001 --title "<short title>" --goal "<worker goal>" --carrier agent_cli --preset deep-research
python3 scripts/lll.py add-task <lll-workdir> --id T002 --title "<dependent task>" --goal "<worker goal>" --depends-on T001
python3 scripts/lll.py status <lll-workdir> --all
python3 scripts/lll.py validate <lll-workdir>
python3 scripts/lll.py validate <lll-workdir> --mode lite
python3 scripts/lll.py validate <lll-workdir> --mode full
```

The helper refuses to reinitialize an existing workdir unless `--force` is explicit. Task output paths must stay under the layout-specific worker root, normally `internal/agents/<task-id>/` for current workdirs.

`add-task --depends-on` is repeatable and also accepts comma-separated lists.

## Strict structure validation checklist

For higher confidence, validate at least:

- required core files exist: `mission.md`, `internal/tasks.jsonl`, `internal/runs.jsonl`, `internal/recovery.json`, `internal/validation.json`, `internal/error-report.jsonl`, `internal/traceability.jsonl`;
- JSON snapshots have the expected schema; JSONL streams parse;
- task ids are unique and non-empty;
- task statuses are one of the runner states (`pending`, `ready`, `leased`, `running`, `verifying`, `succeeded`, `failed_retryable`, `failed_terminal`, `cancelled`) or supported legacy/supervisor aliases (`in_progress`, `blocked`, `done`, `completed`, `failed`);
- dependencies point to existing task ids;
- every task `out` is exactly the layout-specific worker root, normally `internal/agents/<task-id>/`; report files live below it;
- every real task directory has `task.md`, `status.json`, `log.txt`, `handoff.md`, and `artifacts/`;
- task-local `status.json` agrees with the queue where practical;
- no obsolete `output/`, `00-index.md`, or standalone next-step file exists in a new/current workdir;
- canonical `internal/validation.json` and required task-local worker handoffs exist before final delivery.

Even strict structure validation is not mission validation. It only says the recovery surface is coherent enough to inspect.

## Append-only files and token-cost control

Append-only files are useful for auditability but dangerous for context cost if every resume reads them in full.

Treat these as append-only by design:

- `internal/runs.jsonl`
- `internal/error-report.jsonl`
- `internal/traceability.jsonl`
- `internal/logs/supervisor.log` and `internal/logs/runner.log`
- `internal/agents/<task-id>/log.txt`
- optional `internal/**/events.jsonl`, `journal.md`, `history.md` only if explicitly declared append-only

Resume order should prefer compact state first: `mission.md`, `internal/recovery.json`, `internal/tasks.jsonl`, task-local `status.json`, and relevant task-local `handoff.md`. Then read append-only files only by tail, task id, or entries since the last checkpoint. Registry views are derived from tasks/status; do not maintain a duplicate registry file.
