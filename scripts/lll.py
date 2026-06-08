#!/usr/bin/env python3
"""Small stdlib helper for Lin's Living Loop workdirs.

This helper intentionally does not run agents. It only makes the durable file
protocol easy: init, add-task, status, set-status, event, checkpoint, validate.

New workdirs use the canonical v2 layout:
  mission.md + internal/ + output/
Older collab/readable and root-level legacy layouts remain resumable.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

VALID_STATUS = {"pending", "ready", "in_progress", "blocked", "done", "failed", "cancelled"}
LAYOUT_V2 = "v2_internal_output"
LAYOUT_V1 = "v1_collab_readable"
LAYOUT_LEGACY = "legacy_root"
RECOMMENDED_WORKDIR_PATTERN = "~/lll-work/YYYYMMDD_HHMMSS_slug/"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def md_metadata_block(fields: Dict[str, Any]) -> str:
    """Visible Markdown metadata block whose line breaks survive rendering."""
    lines = [f"{key}: {value}" for key, value in fields.items()]
    return "```text\n" + "\n".join(lines) + "\n```\n"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"Invalid JSONL in {path}:{i}: {e}")
    return rows


def write_jsonl_atomic(path: Path, rows: List[Dict[str, Any]]) -> None:
    text = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)
    atomic_write(path, text)


def layout_kind(workdir: Path) -> str:
    """Detect LLL layout while defaulting new/uninitialized workdirs to v2."""
    if (workdir / "internal" / "tasks.jsonl").exists() or ((workdir / "internal").exists() and (workdir / "output").exists()):
        return LAYOUT_V2
    if (workdir / "collab" / "tasks.jsonl").exists() or (workdir / "collab").exists() or (workdir / "readable").exists():
        return LAYOUT_V1
    if any((workdir / name).exists() for name in ["tasks.jsonl", "runs.jsonl", "agent_registry.md", "agents", "deliverables"]):
        return LAYOUT_LEGACY
    return LAYOUT_V2


def is_legacy_layout(workdir: Path) -> bool:
    return layout_kind(workdir) == LAYOUT_LEGACY


def state_dir(workdir: Path) -> Path:
    kind = layout_kind(workdir)
    if kind == LAYOUT_V2:
        return workdir / "internal"
    if kind == LAYOUT_V1:
        return workdir / "collab"
    return workdir


def output_dir(workdir: Path) -> Path:
    kind = layout_kind(workdir)
    if kind == LAYOUT_V2:
        return workdir / "output"
    if kind == LAYOUT_V1:
        return workdir / "readable"
    return workdir / "deliverables"


def recovery_path(workdir: Path) -> Path:
    return state_dir(workdir) / "recovery_state.md" if layout_kind(workdir) == LAYOUT_V2 else workdir / "recovery_state.md"


def handoff_path(workdir: Path) -> Path:
    return state_dir(workdir) / "handoff.md" if layout_kind(workdir) == LAYOUT_V2 else workdir / "handoff.md"


def validation_path(workdir: Path) -> Path:
    return state_dir(workdir) / "validation_report.md" if layout_kind(workdir) == LAYOUT_V2 else workdir / "validation_report.md"


def rel_to_workdir(workdir: Path, path: Path) -> str:
    return path.relative_to(workdir).as_posix()


def tasks_path(workdir: Path) -> Path:
    return state_dir(workdir) / "tasks.jsonl"


def runs_path(workdir: Path) -> Path:
    return state_dir(workdir) / "runs.jsonl"


def registry_path(workdir: Path) -> Path:
    return state_dir(workdir) / "agent_registry.md"


def worker_root_rel(workdir: Path) -> str:
    kind = layout_kind(workdir)
    if kind == LAYOUT_V2:
        return "internal/agents"
    if kind == LAYOUT_V1:
        return "collab/agents"
    return "agents"


def default_task_out(workdir: Path, task_id: str) -> str:
    return f"{worker_root_rel(workdir)}/{task_id}/"


def ensure_safe_relative_out(workdir: Path, out: str, task_id: str | None = None) -> str:
    """Return a normalized relative output dir that cannot escape workdir.

    LLL task outputs must live under the layout-specific worker root:
    internal/agents/<task-id>/ for v2, collab/agents/<task-id>/ for v1,
    or agents/<task-id>/ for legacy workdirs.
    """
    raw = out or ""
    if not raw:
        raise SystemExit("Empty output path")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise SystemExit("--out must be a relative path inside the LLL workdir")
    resolved = (workdir / candidate).resolve()
    try:
        rel_path = resolved.relative_to(workdir)
    except ValueError:
        raise SystemExit("--out must stay inside the LLL workdir")
    parts = rel_path.parts
    kind = layout_kind(workdir)
    if kind == LAYOUT_V2 and len(parts) >= 3 and parts[0] == "internal" and parts[1] == "agents":
        actual_task_id = parts[2]
        allowed = True
    elif kind == LAYOUT_V1 and len(parts) >= 3 and parts[0] == "collab" and parts[1] == "agents":
        actual_task_id = parts[2]
        allowed = True
    elif kind == LAYOUT_LEGACY and len(parts) >= 2 and parts[0] == "agents":
        actual_task_id = parts[1]
        allowed = True
    else:
        allowed = False
        actual_task_id = ""
    if not allowed:
        raise SystemExit(f"--out must be under {worker_root_rel(workdir)}/<task-id>/")
    if task_id is not None and actual_task_id != task_id:
        raise SystemExit(f"--out for task {task_id} must be under {worker_root_rel(workdir)}/{task_id}/")
    return rel_path.as_posix().rstrip("/") + "/"


def write_if_missing_or_force(path: Path, text: str, *, force: bool) -> None:
    if path.exists() and not force:
        return
    if path.exists() and force and path.is_file():
        backup = path.with_name(path.name + ".bak-" + datetime.now().astimezone().strftime("%Y%m%d%H%M%S%z"))
        path.replace(backup)
    atomic_write(path, text)


def event(workdir: Path, *, task_id: str | None, event_name: str, status: str = "info", message: str = "", artifacts: List[str] | None = None, carrier: str = "current", actor: str = "supervisor", exit_code: int | None = None, duration_ms: int | None = None) -> None:
    append_jsonl(runs_path(workdir), {
        "ts": now(),
        "run_id": "R-" + uuid.uuid4().hex[:10],
        "task_id": task_id,
        "actor": actor,
        "carrier": carrier,
        "event": event_name,
        "status": status,
        "message": message,
        "artifacts": artifacts or [],
        "exit_code": exit_code,
        "duration_ms": duration_ms,
    })


def cmd_init(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    for sub in ["internal/logs", "internal/agents", "internal/inputs", "output"]:
        (wd / sub).mkdir(parents=True, exist_ok=True)
    init_ts = now()
    mission = f"""# LLL Mission

```text
mission_id: {wd.name}
created_at: {init_ts}
updated_at: {init_ts}
status: initialized
```

## Objective
{args.objective or '<fill objective>'}

## Success criteria
- <observable criterion>
- output/01_<final-file>.md or another primary output exists when the mission requires it
- internal/validation_report.md is PASS or PASS_WITH_NOTES before final delivery

## Non-goals
- <excluded work>

## Constraints and permissions
- Filesystem writes: {wd}
- Network/API use: <confirm if needed>
- Code execution/background processes: <confirm if needed>
- External services/accounts: <confirm if needed>

## Expected outputs
- output/00_index.md: indexes every file in output/
- output/90_error_report.md: append-only errors/corrections/self-maintenance log; says none if no errors occurred
- output/91_traceability.md: append-only claim/source/change trace map
- output/99_next_steps.md: mutable current next actions for the user
- output/01_<file>.md: primary human-facing deliverable when needed

## Execution policy
- Keep supervisor context small.
- Workers write detailed outputs under internal/agents/<task-id>/.
- Raw inputs, cloned repos, long logs, validation, handoff, and recovery state stay under internal/.
- Human-facing deliverables stay under output/ and use two-digit numeric prefixes.
- Human-facing output body text follows the hidden default: the user-specified output language, or the current interaction language if none is specified. Do not add language metadata labels merely to announce the default; record language only when it is an explicit task constraint. Keep filenames, JSON keys, commands, API names, and code identifiers in English when useful.
- Record state changes in mission.md, internal/tasks.jsonl, internal/runs.jsonl, and internal/recovery_state.md.
- Keep output/00_index.md updated whenever output files are added/removed/renamed.
- Keep output/90_error_report.md and output/91_traceability.md append-only with local-timezone ISO-8601/RFC3339 timestamped entries.
- Rewrite output/99_next_steps.md as the current recommended next action changes.
- Treat internal/runs.jsonl, internal/logs/*.log, and internal/agents/<task-id>/log.txt as append-only; read tails or task/time slices on resume instead of full logs unless needed.
- Use Markdown links for stable references: relative links for files inside this workdir, URLs/absolute paths for stable external resources, and plain text for temporary external files whose location may move.
- Validate before final delivery.

## Recovery quick start
1. Read mission.md.
2. Read internal/recovery_state.md.
3. Inspect mission.md updated_at/status and internal/tasks.jsonl status counts.
4. Read relevant internal/agents/<task-id>/handoff.md files.
5. Read output/00_index.md for human-facing deliverables.
6. Continue from the latest safe checkpoint.
"""
    existing_core = [
        name for name in [
            "mission.md", "internal/tasks.jsonl", "internal/runs.jsonl", "internal/recovery_state.md",
            "collab/tasks.jsonl", "collab/runs.jsonl", "tasks.jsonl", "runs.jsonl", "recovery_state.md",
        ] if (wd / name).exists()
    ]
    if existing_core and not args.force:
        raise SystemExit(
            "LLL workdir already initialized or partially initialized: "
            + ", ".join(existing_core)
            + ". Use --force to reinitialize; existing core files will be backed up where possible."
        )
    write_if_missing_or_force(wd / "mission.md", mission, force=args.force)
    init_files = {
        "internal/tasks.jsonl": "",
        "internal/runs.jsonl": "",
        "internal/agent_registry.md": "# Agent / Worker Registry\n\n| id | role | carrier | preset | status | task(s) | output | notes |\n|---|---|---|---|---|---|---|---|\n| supervisor | decomposes, routes, validates, reports | current | default | active | all | [output/00_index.md](../output/00_index.md) | owns queue and final decisions |\n",
        "internal/validation_report.md": "# Validation Report\n\n```text\nverdict: pending\n```\n",
        "internal/handoff.md": "# Internal LLL Handoff\n\n```text\nstatus: pending\n```\n\n## Main human outputs\n- [output/00_index.md](../output/00_index.md): reading order and links\n",
        "output/00_index.md": "# Output Index\n\nHuman reading order:\n\n1. [00_index.md](00_index.md) — this index; every file in `output/` should be listed here.\n2. [90_error_report.md](90_error_report.md) — append-only workflow/runtime errors, corrections, and self-maintenance notes.\n3. [91_traceability.md](91_traceability.md) — append-only mapping from claims/changes to evidence.\n4. [99_next_steps.md](99_next_steps.md) — current recommended next actions.\n\nAdd primary deliverables such as `01_summary.md` or `01_final_report.md` as they are created. On reuse, update the primary deliverable for same-scope corrections; create `02_*`, `03_*`, etc. for independent new deliverables.\n\nInternal/process files live under [../internal/](../internal/) and are intentionally not the main reading surface.\n",
        "output/90_error_report.md": f"# Error Report\n\n```text\nappend_only: true\ncreated_at: {now()}\nentry_rule: record workflow/runtime abnormalities and repairs, not user goals or normal scope additions; every appended entry includes a local-timezone ISO-8601/RFC3339 timestamp\n```\n\nNo meaningful workflow/runtime errors, corrections, or self-maintenance lessons have been recorded yet. Append timestamped entries below if they occur.\n",
        "output/91_traceability.md": f"# Traceability\n\n```text\nappend_only: true\ncreated_at: {now()}\nentry_rule: every appended entry includes a local-timezone ISO-8601/RFC3339 timestamp\n```\n\nNo claim/source/change trace entries have been recorded yet. Append entries below as outputs and decisions are produced.\n",
        "output/99_next_steps.md": f"# Next Steps\n\n```text\ncurrent_state: active\nupdated_at: {now()}\n```\n\n## Recommended next actions\n\n1. Define or run the next LLL task.\n",
        "internal/logs/supervisor.log": f"{now()} initialized LLL workdir {wd}\n",
        "internal/logs/runner.log": "",
    }
    for name, content in init_files.items():
        write_if_missing_or_force(wd / name, content, force=args.force)
    checkpoint_text = f"""# Recovery State

```text
status: initialized
last_updated: {now()}
current_phase: setup
last_safe_checkpoint: workdir_created
active_tasks: none
blocked_tasks: none
running_processes: none
next_supervisor_action: add or run tasks
```

## Resume steps
1. Read [mission.md](../mission.md).
2. Validate [internal/tasks.jsonl](tasks.jsonl) and [internal/runs.jsonl](runs.jsonl).
3. Read [internal/agent_registry.md](agent_registry.md) and relevant worker handoffs.
4. Read [output/00_index.md](../output/00_index.md) for human-facing outputs.
5. Continue from last_safe_checkpoint.
"""
    write_if_missing_or_force(wd / "internal/recovery_state.md", checkpoint_text, force=args.force)
    event_name = "workdir_reinitialized" if args.force else "workdir_created"
    event(wd, task_id=None, event_name=event_name, status="ok", message="LLL workdir initialized", artifacts=["mission.md", rel_to_workdir(wd, tasks_path(wd)), "output/00_index.md", "output/90_error_report.md", "output/91_traceability.md", "output/99_next_steps.md"])
    print(wd)


def cmd_add_task(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    tasks = read_jsonl(tasks_path(wd))
    if any(t.get("id") == args.id for t in tasks):
        raise SystemExit(f"Task already exists: {args.id}")
    out = ensure_safe_relative_out(wd, args.out or default_task_out(wd, args.id), args.id)
    task = {
        "id": args.id,
        "title": args.title,
        "status": "pending",
        "priority": args.priority,
        "depends_on": args.depends_on or [],
        "carrier": args.carrier,
        "preset": args.preset,
        "attempts": 0,
        "max_attempts": args.max_attempts,
        "out": out,
        "goal": args.goal,
        "acceptance": args.acceptance or ["handoff.md written"],
        "inputs": args.inputs or ["mission.md"],
        "created_at": now(),
        "updated_at": now(),
        "claim_id": None,
        "lease_until": None,
        "error": None,
    }
    tasks.append(task)
    tasks.sort(key=lambda x: (-int(x.get("priority", 0)), str(x.get("id", ""))))
    write_jsonl_atomic(tasks_path(wd), tasks)
    task_dir = wd / out
    (task_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    kind = layout_kind(wd)
    if kind == LAYOUT_V2:
        shared_files = "[internal/tasks.jsonl](../../tasks.jsonl), [internal/runs.jsonl](../../runs.jsonl), [internal/agent_registry.md](../../agent_registry.md), [internal/recovery_state.md](../../recovery_state.md)"
        mission_link = "[mission.md](../../../mission.md)"
        output_link = "[output/](../../../output/)"
    elif kind == LAYOUT_V1:
        shared_files = "[collab/tasks.jsonl](../../tasks.jsonl), [collab/runs.jsonl](../../runs.jsonl), [collab/agent_registry.md](../../agent_registry.md), [recovery_state.md](../../../recovery_state.md)"
        mission_link = "[mission.md](../../../mission.md)"
        output_link = "[readable/](../../../readable/)"
    else:
        shared_files = "[tasks.jsonl](../../tasks.jsonl), [runs.jsonl](../../runs.jsonl), [agent_registry.md](../../agent_registry.md), [recovery_state.md](../../recovery_state.md)"
        mission_link = "[mission.md](../../mission.md)"
        output_link = "[deliverables/](../../deliverables/) or a supervisor-assigned human-facing path"
    input_lines = []
    for item in task["inputs"]:
        if item == "mission.md":
            input_lines.append(f"- {mission_link}\n")
        else:
            input_lines.append(f"- {item}\n")
    atomic_write(task_dir / "task.md", f"# LLL Worker Task\n\n```text\ntask_id: {args.id}\ncarrier: {args.carrier}\npreset: {args.preset}\nstatus: pending\n```\n\n## Objective\n{args.goal}\n\n## Inputs\n" + "".join(input_lines) + "\n## Required outputs\n- [handoff.md](handoff.md)\n- [artifacts/](artifacts/) as needed\n\n## Compact LLL contract\n- Read " + mission_link + ", this task file, and listed inputs before starting.\n- Treat the workdir as the source of truth; chat is only a short handoff.\n- Write detailed work, logs, evidence, drafts, and outputs under this task directory unless explicitly assigned a shared human-facing deliverable under " + output_link + ".\n- Write an artifact skeleton early, then fill it incrementally for long reading/research tasks.\n- Do not edit shared state files (" + shared_files + ") unless explicitly granted ownership through a lock or runner API.\n- Keep claims traceable to artifact paths, sources, commands, or validation notes; use Markdown links for stable references.\n- If writing human-facing outputs, use numbered filenames under " + output_link + " and make sure 00_index.md is updated by the owner/supervisor.\n- If blocked, record what was tried and propose the smallest fallback.\n\n## Logging\nAppend commands, sources, decisions, failures, and retries to [log.txt](log.txt).\n\n## Handoff contract\nstatus, outputs, 1-3 key results, risks/blockers, recommended next step\n")
    atomic_write(task_dir / "status.json", json.dumps({"task_id": args.id, "status": "pending", "current_step": "not started", "attempts": 0, "last_checkpoint": None, "last_error": None, "outputs": [], "updated_at": now()}, ensure_ascii=False, indent=2) + "\n")
    atomic_write(task_dir / "log.txt", f"{now()} task queued\n")
    atomic_write(task_dir / "handoff.md", f"# Worker Handoff\n\n```text\nstatus: pending\ntask_id: {args.id}\n```\n")
    event(wd, task_id=args.id, event_name="queued", status="ok", message=args.title, artifacts=[out + "task.md"])
    print(f"added {args.id} -> {out}")


def cmd_status(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    tasks = read_jsonl(tasks_path(wd))
    counts: Dict[str, int] = {}
    for t in tasks:
        counts[t.get("status", "unknown")] = counts.get(t.get("status", "unknown"), 0) + 1
    print(f"workdir: {wd}")
    print(f"layout: {layout_kind(wd)}")
    print("tasks:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none")
    for t in tasks:
        if args.all or t.get("status") not in {"done", "cancelled"}:
            print(f"{t.get('id')} [{t.get('status')}] p{t.get('priority')} {t.get('carrier')}/{t.get('preset')} - {t.get('title')}")


def cmd_set_status(args: argparse.Namespace) -> None:
    if args.status not in VALID_STATUS:
        raise SystemExit(f"Invalid status: {args.status}")
    wd = Path(args.workdir).expanduser().resolve()
    tasks = read_jsonl(tasks_path(wd))
    found = False
    out = None
    for t in tasks:
        if t.get("id") == args.id:
            found = True
            t["status"] = args.status
            t["updated_at"] = now()
            if args.error:
                t["error"] = args.error
            out = ensure_safe_relative_out(wd, t.get("out") or default_task_out(wd, args.id), args.id)
            t["out"] = out
            break
    if not found:
        raise SystemExit(f"No such task: {args.id}")
    write_jsonl_atomic(tasks_path(wd), tasks)
    status_path = wd / out / "status.json"
    cur = {}
    if status_path.exists():
        try:
            cur = json.loads(status_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cur = {}
    cur.update({"task_id": args.id, "status": args.status, "current_step": args.note or args.status, "last_error": args.error, "updated_at": now()})
    atomic_write(status_path, json.dumps(cur, ensure_ascii=False, indent=2) + "\n")
    event(wd, task_id=args.id, event_name="status", status="ok", message=args.note or args.status, artifacts=[str(Path(out) / "status.json")])
    print(f"{args.id} -> {args.status}")


def cmd_event(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    event(wd, task_id=args.task_id, event_name=args.event, status=args.status, message=args.message or "", artifacts=args.artifact or [], carrier=args.carrier, actor=args.actor)
    print("event appended")


def cmd_checkpoint(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    tasks = read_jsonl(tasks_path(wd))
    active = [t["id"] for t in tasks if t.get("status") == "in_progress"]
    blocked = [t["id"] for t in tasks if t.get("status") == "blocked"]
    task_rel = rel_to_workdir(wd, tasks_path(wd))
    runs_rel = rel_to_workdir(wd, runs_path(wd))
    registry_rel = rel_to_workdir(wd, registry_path(wd))
    output_index = output_dir(wd) / "00_index.md"
    output_rel = rel_to_workdir(wd, output_index) if output_index.exists() else rel_to_workdir(wd, output_dir(wd))
    text = f"""# Recovery State

```text
status: {args.status}
last_updated: {now()}
current_phase: {args.phase}
last_safe_checkpoint: {args.checkpoint}
active_tasks: {', '.join(active) if active else 'none'}
blocked_tasks: {', '.join(blocked) if blocked else 'none'}
running_processes: {args.running or 'unknown/none'}
next_supervisor_action: {args.next_action}
```

## Resume steps
1. Read [mission.md](../mission.md) if this file is under internal/, otherwise `mission.md` in the workdir root.
2. Validate [{task_rel}]({Path(task_rel).name if layout_kind(wd) == LAYOUT_V2 else task_rel}) and [{runs_rel}]({Path(runs_rel).name if layout_kind(wd) == LAYOUT_V2 else runs_rel}).
3. Read [{registry_rel}]({Path(registry_rel).name if layout_kind(wd) == LAYOUT_V2 else registry_rel}) and relevant worker handoffs.
4. Read [{output_rel}]({('../' + output_rel) if layout_kind(wd) == LAYOUT_V2 else output_rel}) for human-facing outputs.
5. Continue from last_safe_checkpoint.
"""
    atomic_write(recovery_path(wd), text)
    event(wd, task_id=None, event_name="checkpoint", status="ok", message=args.checkpoint, artifacts=[rel_to_workdir(wd, recovery_path(wd))])
    print("checkpoint updated")


def validate_output_index(wd: Path) -> bool:
    kind = layout_kind(wd)
    outdir = output_dir(wd)
    if not outdir.exists():
        if kind == LAYOUT_V2:
            print(f"missing: {rel_to_workdir(wd, outdir)}")
            return False
        return True
    index = outdir / "00_index.md"
    if not index.exists():
        if kind == LAYOUT_V2 or any(outdir.iterdir()):
            print(f"missing: {rel_to_workdir(wd, index)}")
            return False
        return True
    text = index.read_text(encoding="utf-8", errors="replace")
    ok = True
    for path in sorted(p for p in outdir.iterdir() if p.is_file()):
        if path.name not in text:
            ok = False
            print(f"output index does not mention {rel_to_workdir(wd, path)}")
    if kind == LAYOUT_V2:
        for name in ["90_error_report.md", "91_traceability.md", "99_next_steps.md"]:
            p = outdir / name
            if not p.exists():
                ok = False
                print(f"missing: {rel_to_workdir(wd, p)}")
            elif name not in text:
                ok = False
                print(f"output index does not mention {rel_to_workdir(wd, p)}")
    return ok


def cmd_validate(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    kind = layout_kind(wd)
    required = [
        "mission.md",
        rel_to_workdir(wd, recovery_path(wd)),
        rel_to_workdir(wd, tasks_path(wd)),
        rel_to_workdir(wd, runs_path(wd)),
        rel_to_workdir(wd, registry_path(wd)),
    ]
    if kind == LAYOUT_V2:
        required.extend([rel_to_workdir(wd, handoff_path(wd)), rel_to_workdir(wd, validation_path(wd))])
    ok = True
    for rel in required:
        if not (wd / rel).exists():
            ok = False
            print(f"missing: {rel}")
    for rel in [rel_to_workdir(wd, tasks_path(wd)), rel_to_workdir(wd, runs_path(wd))]:
        try:
            read_jsonl(wd / rel)
        except SystemExit as e:
            ok = False
            print(e)
    tasks = read_jsonl(tasks_path(wd)) if tasks_path(wd).exists() else []
    seen: set[str] = set()
    ids: set[str] = set()
    for t in tasks:
        task_id = t.get("id")
        if not isinstance(task_id, str) or not task_id:
            ok = False
            print("task with missing/invalid id")
            continue
        if task_id in seen:
            ok = False
            print(f"duplicate task id {task_id}")
        seen.add(task_id)
        ids.add(task_id)
    for t in tasks:
        task_id = t.get("id")
        if not isinstance(task_id, str) or not task_id:
            continue
        status = t.get("status")
        if status not in VALID_STATUS:
            ok = False
            print(f"task {task_id} has invalid status {status}")
        for dep in t.get("depends_on", []) or []:
            if dep not in ids:
                ok = False
                print(f"task {task_id} has missing dependency {dep}")
        try:
            out = ensure_safe_relative_out(wd, t.get("out") or default_task_out(wd, task_id), task_id)
        except SystemExit as e:
            ok = False
            print(f"task {task_id} has invalid out path: {e}")
            continue
        task_dir = wd / out
        if not task_dir.exists():
            ok = False
            print(f"task {task_id} missing output dir {out}")
        for rel in ["task.md", "status.json", "log.txt", "handoff.md", "artifacts"]:
            if not (task_dir / rel).exists():
                ok = False
                print(f"task {task_id} missing {out}{rel}")
        status_path = task_dir / "status.json"
        if status_path.exists():
            try:
                local_status = json.loads(status_path.read_text(encoding="utf-8"))
                if local_status.get("status") and local_status.get("status") != status:
                    print(f"note: task {task_id} queue status {status} differs from local status {local_status.get('status')}")
            except json.JSONDecodeError as e:
                ok = False
                print(f"task {task_id} invalid status.json: {e}")
    if not validate_output_index(wd):
        ok = False
    if ok:
        print(f"LLL workdir structure valid ({kind})")
    else:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="LLL file-protocol helper",
        epilog=f"Recommended new workdir pattern: {RECOMMENDED_WORKDIR_PATTERN} (underscore between date and time; do not use YYYYMMDD-HHMMSS).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create a LLL v2 workdir: mission.md + internal/ + output/; recommended path: YYYYMMDD_HHMMSS_slug")
    s.add_argument("workdir")
    s.add_argument("--objective", default="")
    s.add_argument("--force", action="store_true", help="reinitialize an existing workdir after backing up overwritten core files where possible")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("add-task", help="add a task to the layout-specific queue and create the worker directory")
    s.add_argument("workdir")
    s.add_argument("--id", required=True)
    s.add_argument("--title", required=True)
    s.add_argument("--goal", required=True)
    s.add_argument("--carrier", default="current")
    s.add_argument("--preset", default="default")
    s.add_argument("--priority", type=int, default=10)
    s.add_argument("--depends-on", action="append", default=[])
    s.add_argument("--acceptance", action="append", default=[])
    s.add_argument("--inputs", action="append", default=[])
    s.add_argument("--max-attempts", type=int, default=2)
    s.add_argument("--out", default="")
    s.set_defaults(func=cmd_add_task)

    s = sub.add_parser("status", help="show task status summary")
    s.add_argument("workdir")
    s.add_argument("--all", action="store_true")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("set-status", help="update one task status")
    s.add_argument("workdir")
    s.add_argument("id")
    s.add_argument("status")
    s.add_argument("--note", default="")
    s.add_argument("--error", default=None)
    s.set_defaults(func=cmd_set_status)

    s = sub.add_parser("event", help="append an event to the layout-specific runs.jsonl")
    s.add_argument("workdir")
    s.add_argument("--task-id", default=None)
    s.add_argument("--event", required=True)
    s.add_argument("--status", default="info")
    s.add_argument("--message", default="")
    s.add_argument("--artifact", action="append", default=[])
    s.add_argument("--carrier", default="current")
    s.add_argument("--actor", default="supervisor")
    s.set_defaults(func=cmd_event)

    s = sub.add_parser("checkpoint", help="rewrite the layout-specific recovery_state.md")
    s.add_argument("workdir")
    s.add_argument("--status", default="active")
    s.add_argument("--phase", default="working")
    s.add_argument("--checkpoint", default="manual_checkpoint")
    s.add_argument("--next-action", default="continue next task")
    s.add_argument("--running", default="")
    s.set_defaults(func=cmd_checkpoint)

    s = sub.add_parser("validate", help="validate required files, JSONL, task dirs, and output index")
    s.add_argument("workdir")
    s.set_defaults(func=cmd_validate)

    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
