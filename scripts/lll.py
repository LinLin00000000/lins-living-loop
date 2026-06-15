#!/usr/bin/env python3
"""Small stdlib helper for Lin's Living Loop workdirs.

This helper intentionally does not run agents. It only makes the durable file
protocol easy: init, add-task, status, set-status, event, checkpoint, validate.

New workdirs use the compact current layout:
  mission.md + top-level human deliverables + internal/

Human-facing artifacts named from the task, such as `architecture-options.md` or `validation-summary.md`, live beside `mission.md`.
Process state, worker state, validation, traceability, and error logs live under
`internal/`. The old `output/` navigation layer is intentionally not generated.
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
LAYOUT_CURRENT = "current_internal_root_outputs"
LAYOUT_LEGACY = "legacy_or_transitional"
RECOMMENDED_WORKDIR_PATTERN = "~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/"

AGENT_REGISTRY = "agent-registry.md"
RECOVERY_STATE = "recovery-state.md"
VALIDATION_REPORT = "validation-report.md"
ERROR_REPORT_JSONL = "error-report.jsonl"
TRACEABILITY_JSONL = "traceability.jsonl"
ALIASES = {
    AGENT_REGISTRY: ["agent_registry.md"],
    RECOVERY_STATE: ["recovery_state.md"],
    VALIDATION_REPORT: ["validation_report.md"],
}


def existing_or_canonical(directory: Path, canonical: str) -> Path:
    canonical_path = directory / canonical
    if canonical_path.exists():
        return canonical_path
    for alias in ALIASES.get(canonical, []):
        alias_path = directory / alias
        if alias_path.exists():
            return alias_path
    return canonical_path


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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


def normalize_depends_on(values: List[str] | None) -> List[str]:
    deps: List[str] = []
    seen = set()
    for value in values or []:
        for dep in str(value).split(","):
            dep = dep.strip()
            if dep and dep not in seen:
                deps.append(dep)
                seen.add(dep)
    return deps


def layout_kind(workdir: Path) -> str:
    """Detect only enough layout to avoid breaking obvious resumes.

    New workdirs are current-layout. Old transitional/legacy trees are not
    migrated or elaborately normalized; helper commands use broad, loose paths
    when they are detected.
    """
    if (workdir / "internal").exists() or (workdir / "mission.md").exists():
        return LAYOUT_CURRENT
    if any((workdir / name).exists() for name in ["collab", "readable", "deliverables", "tasks.jsonl", "runs.jsonl", "agents"]):
        return LAYOUT_LEGACY
    return LAYOUT_CURRENT


def state_dir(workdir: Path) -> Path:
    if layout_kind(workdir) == LAYOUT_CURRENT:
        return workdir / "internal"
    if (workdir / "collab").exists():
        return workdir / "collab"
    return workdir


def recovery_path(workdir: Path) -> Path:
    if layout_kind(workdir) == LAYOUT_CURRENT:
        return existing_or_canonical(state_dir(workdir), RECOVERY_STATE)
    return existing_or_canonical(workdir, RECOVERY_STATE)


def handoff_path(workdir: Path) -> Path:
    if layout_kind(workdir) == LAYOUT_CURRENT:
        return state_dir(workdir) / "handoff.md"
    return workdir / "handoff.md"


def validation_path(workdir: Path) -> Path:
    if layout_kind(workdir) == LAYOUT_CURRENT:
        return existing_or_canonical(state_dir(workdir), VALIDATION_REPORT)
    return existing_or_canonical(workdir, VALIDATION_REPORT)


def tasks_path(workdir: Path) -> Path:
    return state_dir(workdir) / "tasks.jsonl"


def runs_path(workdir: Path) -> Path:
    return state_dir(workdir) / "runs.jsonl"


def registry_path(workdir: Path) -> Path:
    return existing_or_canonical(state_dir(workdir), AGENT_REGISTRY)


def error_report_path(workdir: Path) -> Path:
    return state_dir(workdir) / ERROR_REPORT_JSONL


def traceability_path(workdir: Path) -> Path:
    return state_dir(workdir) / TRACEABILITY_JSONL


def worker_root_rel(workdir: Path) -> str:
    if layout_kind(workdir) == LAYOUT_CURRENT:
        return "internal/agents"
    if (workdir / "collab").exists():
        return "collab/agents"
    return "agents"


def default_task_out(workdir: Path, task_id: str) -> str:
    return f"{worker_root_rel(workdir)}/{task_id}/"


def rel_to_workdir(workdir: Path, path: Path) -> str:
    return path.relative_to(workdir).as_posix()


def ensure_safe_relative_out(workdir: Path, out: str, task_id: str | None = None) -> str:
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
    root = worker_root_rel(workdir).split("/")
    if len(parts) < len(root) + 1 or list(parts[: len(root)]) != root:
        raise SystemExit(f"--out must be under {worker_root_rel(workdir)}/<task-id>/")
    actual_task_id = parts[len(root)]
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


def event(
    workdir: Path,
    *,
    task_id: str | None,
    event_name: str,
    status: str = "info",
    message: str = "",
    artifacts: List[str] | None = None,
    carrier: str = "current",
    actor: str = "supervisor",
    exit_code: int | None = None,
    duration_ms: int | None = None,
) -> None:
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
    for sub in ["internal/logs", "internal/agents", "internal/inputs"]:
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
- a top-level mission-specific deliverable exists when needed, named from the task rather than a fixed deliverable template
- `internal/validation-report.md` is PASS or PASS_WITH_NOTES before final delivery

## Non-goals
- <excluded work>

## Constraints and permissions
- Filesystem writes: {wd}
- Network/API use: <confirm if needed>
- Code execution/background processes: <confirm if needed>
- External services/accounts: <confirm if needed>

## Expected outputs
- Top-level human-facing deliverable(s) with task-specific names; merge into one Markdown file when that preserves thematic completeness, or split into multiple clearly named files when the content has multiple independent themes or becomes too large.
- Next steps are a section inside the primary deliverable or the relevant deliverable, not a separate `Next Step.md` / `99-next-steps.md` file.
- `internal/error-report.jsonl`: append-only workflow/runtime abnormalities, repairs, and self-maintenance events.
- `internal/traceability.jsonl`: append-only claim/source/change trace entries.

## Execution policy
- Keep supervisor context small.
- Workers write detailed outputs under `internal/agents/<task-id>/`.
- Raw inputs, cloned repos, long logs, validation, handoff, recovery state, traceability, and error logs stay under `internal/`.
- Human-facing deliverables live at the workdir root beside `mission.md`; name them from the task/content rather than using numeric prefixes or generic report titles.
- Do not create `output/`, `00-index.md`, or standalone next-step files for new workdirs.
- Human-facing output body text follows the hidden default: the user-specified output language, or the current interaction language if none is specified. Do not add language metadata labels merely to announce the default; record language only when it is an explicit task constraint. Keep filenames, JSON keys, commands, API names, and code identifiers in English when useful.
- Record state changes in `mission.md`, `internal/tasks.jsonl`, `internal/runs.jsonl`, and `internal/recovery-state.md`.
- Append traceability and error entries as JSONL objects with local-timezone ISO-8601/RFC3339 timestamps; do not reread the whole log just to append.
- Treat `internal/runs.jsonl`, `internal/error-report.jsonl`, `internal/traceability.jsonl`, `internal/logs/*.log`, and `internal/agents/<task-id>/log.txt` as append-only; read tails or task/time slices on resume instead of full logs unless needed.
- Use Markdown links for stable references: relative links for files inside this workdir, URLs/absolute paths for stable external resources, and plain text for temporary external files whose location may move.
- Validate before final delivery.

## Recovery quick start
1. Read `mission.md`.
2. Read `internal/recovery-state.md`.
3. Inspect `internal/tasks.jsonl` status counts.
4. Read relevant `internal/agents/<task-id>/handoff.md` files.
5. Read top-level task-specific deliverables; inspect JSONL audit tails only as needed.
6. Continue from the latest safe checkpoint.
"""
    existing_core = [
        name for name in [
            "mission.md", "internal/tasks.jsonl", "internal/runs.jsonl", "internal/recovery-state.md", "internal/recovery_state.md",
            "tasks.jsonl", "runs.jsonl", "recovery-state.md", "recovery_state.md",
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
        "internal/agent-registry.md": "# Agent / Worker Registry\n\n| id | role | carrier | preset | status | task(s) | output | notes |\n|---|---|---|---|---|---|---|---|\n| supervisor | decomposes, routes, validates, reports | current | default | active | all | root task-specific deliverables as needed | owns queue and final decisions |\n",
        "internal/validation-report.md": "# Validation Report\n\n```text\nverdict: pending\n```\n\n## Structure checks\n\n| check | status | evidence |\n|---|---|---|\n| required current-layout files exist | pending | [mission](../mission.md), [internal queue](tasks.jsonl), [traceability](traceability.jsonl), [error report](error-report.jsonl) |\n| obsolete output layer absent | pending | no `output/`, `00-index.md`, or standalone next-step file generated |\n| human-facing deliverables are top-level | pending | primary task-specific root deliverable(s), when required by mission |\n| human-facing output language is correct | pending | primary deliverable body follows requested/current interaction language |\n\n## Mission criteria check\n\n| criterion | status | evidence |\n|---|---|---|\n| <criterion> | pending | <path/link> |\n",
        "internal/handoff.md": "# Internal LLL Handoff\n\n```text\nstatus: pending\n```\n\n## Main human outputs\n- Top-level task-specific deliverables beside `mission.md`, when created.\n- Current next steps belong inside the primary deliverable/relevant deliverable.\n",
        "internal/logs/supervisor.log": f"{now()} initialized LLL workdir {wd}\n",
        "internal/logs/runner.log": "",
    }
    for name, content in init_files.items():
        write_if_missing_or_force(wd / name, content, force=args.force)
    for rel, kind, note in [
        ("internal/error-report.jsonl", "error_report", "No workflow/runtime errors recorded yet; append only if an issue occurs."),
        ("internal/traceability.jsonl", "traceability", "Trace entries append here as claims, sources, changes, and validation evidence appear."),
    ]:
        p = wd / rel
        if not p.exists() or args.force:
            append_jsonl(p, {"ts": init_ts, "type": "init", "kind": kind, "note": note})
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
3. Read [internal/agent-registry.md](agent-registry.md) and relevant worker handoffs.
4. Read top-level task-specific deliverables when present; read `traceability.jsonl` / `error-report.jsonl` tails only as needed.
5. Continue from last_safe_checkpoint.
"""
    write_if_missing_or_force(wd / "internal/recovery-state.md", checkpoint_text, force=args.force)
    event_name = "workdir_reinitialized" if args.force else "workdir_created"
    event(wd, task_id=None, event_name=event_name, status="ok", message="LLL workdir initialized", artifacts=["mission.md", rel_to_workdir(wd, tasks_path(wd)), "internal/error-report.jsonl", "internal/traceability.jsonl"])
    print(wd)


def cmd_add_task(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    tasks = read_jsonl(tasks_path(wd))
    if any(t.get("id") == args.id for t in tasks):
        raise SystemExit(f"Task already exists: {args.id}")
    out = ensure_safe_relative_out(wd, args.out or default_task_out(wd, args.id), args.id)
    depends_on = normalize_depends_on(args.depends_on)
    task = {
        "id": args.id,
        "title": args.title,
        "status": "pending",
        "priority": args.priority,
        "depends_on": depends_on,
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

    def link_to(path: Path, label: str | None = None) -> str:
        rel = os.path.relpath(path, start=task_dir).replace(os.sep, "/")
        return f"[{label or rel}]({rel})"

    shared_files = ", ".join([
        link_to(tasks_path(wd), rel_to_workdir(wd, tasks_path(wd))),
        link_to(runs_path(wd), rel_to_workdir(wd, runs_path(wd))),
        link_to(registry_path(wd), rel_to_workdir(wd, registry_path(wd))),
        link_to(recovery_path(wd), rel_to_workdir(wd, recovery_path(wd))),
        link_to(traceability_path(wd), rel_to_workdir(wd, traceability_path(wd))),
        link_to(error_report_path(wd), rel_to_workdir(wd, error_report_path(wd))),
    ])
    mission_link = link_to(wd / "mission.md", "mission.md")
    root_output_link = "[workdir root](../../../)" if layout_kind(wd) == LAYOUT_CURRENT else "the supervisor-assigned human-facing path"
    input_lines = []
    for item in task["inputs"]:
        if item == "mission.md":
            input_lines.append(f"- {mission_link}\n")
        else:
            input_lines.append(f"- {item}\n")
    atomic_write(task_dir / "task.md", f"# LLL Worker Task\n\n```text\ntask_id: {args.id}\ncarrier: {args.carrier}\npreset: {args.preset}\nstatus: pending\n```\n\n## Objective\n{args.goal}\n\n## Inputs\n" + "".join(input_lines) + "\n## Required outputs\n- [handoff.md](handoff.md)\n- [artifacts/](artifacts/) as needed\n\n## Compact LLL contract\n- Read " + mission_link + ", this task file, and listed inputs before starting.\n- Treat the workdir as the source of truth; chat is only a short handoff.\n- Write detailed work, logs, evidence, drafts, and outputs under this task directory unless explicitly assigned a shared human-facing deliverable at " + root_output_link + ".\n- Human-facing deliverables should use task-specific filenames at the workdir root; merge when one file preserves thematic completeness, split into clearly named files only when content or themes justify it.\n- Current next steps belong inside the primary deliverable/relevant deliverable, not in a standalone next-step file.\n- Write an artifact skeleton early, then fill it incrementally for long reading/research tasks.\n- Do not edit shared state files (" + shared_files + ") unless explicitly granted ownership through a lock or runner API.\n- Keep claims traceable to artifact paths, sources, commands, or validation notes; append JSONL trace entries only when assigned/authorized.\n- If blocked, record what was tried and propose the smallest fallback.\n\n## Logging\nAppend commands, sources, decisions, failures, and retries to [log.txt](log.txt).\n\n## Handoff contract\nstatus, outputs, 1-3 key results, risks/blockers, recommended next step\n")
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
2. Validate [{task_rel}]({Path(task_rel).name if layout_kind(wd) == LAYOUT_CURRENT else task_rel}) and [{runs_rel}]({Path(runs_rel).name if layout_kind(wd) == LAYOUT_CURRENT else runs_rel}).
3. Read [{registry_rel}]({Path(registry_rel).name if layout_kind(wd) == LAYOUT_CURRENT else registry_rel}) and relevant worker handoffs.
4. Read top-level task-specific deliverables; inspect `traceability.jsonl` / `error-report.jsonl` tails only as needed.
5. Continue from last_safe_checkpoint.
"""
    atomic_write(recovery_path(wd), text)
    event(wd, task_id=None, event_name="checkpoint", status="ok", message=args.checkpoint, artifacts=[rel_to_workdir(wd, recovery_path(wd))])
    print("checkpoint updated")


def detect_validation_mode(wd: Path, requested: str) -> str:
    if requested in {"full", "lite"}:
        return requested
    if tasks_path(wd).exists():
        return "full"
    if (wd / "mission.md").exists():
        return "lite"
    return "full"


def validate_current_surface(wd: Path, *, mode: str) -> bool:
    ok = True
    obsolete = ["output", "00-index.md", "00_index.md", "99-next-steps.md", "99_next_steps.md", "Next Step.md", "Next Steps.md"]
    for name in obsolete:
        p = wd / name
        if p.exists():
            ok = False
            print(f"obsolete current-layout surface exists: {rel_to_workdir(wd, p)}")
    if mode != "lite":
        for p in [error_report_path(wd), traceability_path(wd)]:
            if not p.exists():
                ok = False
                print(f"missing: {rel_to_workdir(wd, p)}")
                continue
            try:
                read_jsonl(p)
            except SystemExit as e:
                ok = False
                print(e)
    return ok


def cmd_validate(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    kind = layout_kind(wd)
    mode = detect_validation_mode(wd, args.mode)
    required = ["mission.md"]
    if mode == "lite":
        has_compact_surface = (wd / "notes.md").exists() or validation_path(wd).exists() or any(wd.glob("[0-9][0-9]-*.md"))
        if not has_compact_surface:
            required.append("notes.md")
    else:
        required.extend([
            rel_to_workdir(wd, recovery_path(wd)),
            rel_to_workdir(wd, tasks_path(wd)),
            rel_to_workdir(wd, runs_path(wd)),
            rel_to_workdir(wd, registry_path(wd)),
        ])
        if kind == LAYOUT_CURRENT:
            required.extend([
                rel_to_workdir(wd, handoff_path(wd)),
                rel_to_workdir(wd, validation_path(wd)),
                rel_to_workdir(wd, error_report_path(wd)),
                rel_to_workdir(wd, traceability_path(wd)),
            ])
    ok = True
    for rel in required:
        if not (wd / rel).exists():
            ok = False
            print(f"missing: {rel}")
    jsonl_paths = []
    for pth in [tasks_path(wd), runs_path(wd), error_report_path(wd), traceability_path(wd)]:
        if mode != "lite" or pth.exists():
            jsonl_paths.append(rel_to_workdir(wd, pth))
    for rel in jsonl_paths:
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
        if mode == "lite" and not t.get("out"):
            continue
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
    if kind == LAYOUT_CURRENT and not validate_current_surface(wd, mode=mode):
        ok = False
    if ok:
        print(f"LLL workdir structure valid ({kind}, {mode})")
    else:
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="LLL file-protocol helper",
        epilog=f"Recommended new workdir pattern: {RECOMMENDED_WORKDIR_PATTERN} (hyphen inside timestamp, underscore before the kebab-case short description; do not use YYYYMMDD_HHMMSS_slug for new workdirs).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser(
        "init",
        help="create a LLL workdir: mission.md + top-level deliverables + internal/; recommended path: YYYYMMDD-HHMMSS_short-description-in-kebab-case",
        description="Create a LLL workdir: mission.md + top-level human deliverables + internal/.",
        epilog=f"Recommended new workdir pattern: {RECOMMENDED_WORKDIR_PATTERN}",
    )
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
    s.add_argument("--depends-on", action="append", default=[], help="dependency task id; repeat for multiple dependencies, or pass a comma-separated list")
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

    s = sub.add_parser("checkpoint", help="rewrite the layout-specific recovery-state.md")
    s.add_argument("workdir")
    s.add_argument("--status", default="active")
    s.add_argument("--phase", default="working")
    s.add_argument("--checkpoint", default="manual_checkpoint")
    s.add_argument("--next-action", default="continue next task")
    s.add_argument("--running", default="")
    s.set_defaults(func=cmd_checkpoint)

    s = sub.add_parser("validate", help="validate required files, JSONL, task dirs, and compact current layout")
    s.add_argument("workdir")
    s.add_argument("--mode", choices=["auto", "full", "lite"], default="auto", help="validation mode: auto detects honest Lite workdirs, full keeps strict worker-tree checks")
    s.set_defaults(func=cmd_validate)

    return p


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
