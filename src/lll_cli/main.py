#!/usr/bin/env python3
"""Lin's Living Loop (`lll`) CLI.

Stdlib-only reference implementation for the LLL file protocol plus a small
agent-agnostic runner. The CLI intentionally stays boring: plain files, JSONL,
subprocess adapters, and generated service wrappers rather than a database,
server, dashboard, or planning brain.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

try:
    from . import __version__
except ImportError:  # pragma: no cover - direct source-file execution fallback
    __version__ = "0.1.0"

VALID_STATUS = {
    "pending", "ready", "leased", "running", "verifying", "succeeded",
    "failed_retryable", "failed_terminal", "cancelled",
    # Legacy/supervisor aliases kept for existing workdirs.
    "in_progress", "blocked", "done", "failed",
}
CLAIMABLE_STATUS = {"pending", "ready", "failed_retryable"}
ACTIVE_STATUS = {"leased", "running", "verifying", "in_progress"}
LAYOUT_CURRENT = "current_internal_root_outputs"
LAYOUT_LEGACY = "legacy_or_transitional"
RECOMMENDED_WORKDIR_PATTERN = "~/lll-work/YYYYMMDD-HHMMSS_short-description-in-kebab-case/"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex[:8])
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f"Invalid JSONL in {path}:{i}: {e}")
            if not isinstance(value, dict):
                raise SystemExit(f"Invalid JSONL in {path}:{i}: expected object")
            rows.append(value)
    return rows


def write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    atomic_write(path, "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows))


def layout_kind(workdir: Path) -> str:
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


def tasks_path(workdir: Path) -> Path:
    return state_dir(workdir) / "tasks.jsonl"


def runs_path(workdir: Path) -> Path:
    return state_dir(workdir) / "runs.jsonl"


def registry_path(workdir: Path) -> Path:
    return state_dir(workdir) / "agent-registry.md"


def recovery_path(workdir: Path) -> Path:
    return state_dir(workdir) / "recovery-state.md"


def handoff_path(workdir: Path) -> Path:
    return state_dir(workdir) / "handoff.md"


def validation_path(workdir: Path) -> Path:
    return state_dir(workdir) / "validation-report.md"


def error_report_path(workdir: Path) -> Path:
    return state_dir(workdir) / "error-report.jsonl"


def traceability_path(workdir: Path) -> Path:
    return state_dir(workdir) / "traceability.jsonl"


def config_path(workdir: Path) -> Path:
    return state_dir(workdir) / "lll-config.json"


def worker_root_rel(workdir: Path) -> str:
    if layout_kind(workdir) == LAYOUT_CURRENT:
        return "internal/agents"
    if (workdir / "collab").exists():
        return "collab/agents"
    return "agents"


def default_task_out(workdir: Path, task_id: str) -> str:
    return f"{worker_root_rel(workdir)}/{task_id}/"


def rel_to_workdir(workdir: Path, path: Path) -> str:
    return path.resolve().relative_to(workdir.resolve()).as_posix()


def ensure_safe_relative_out(workdir: Path, out: str, task_id: str | None = None) -> str:
    if not out:
        raise SystemExit("empty output path")
    candidate = Path(out)
    if candidate.is_absolute():
        raise SystemExit("output path must be relative to the LLL workdir")
    resolved = (workdir / candidate).resolve()
    try:
        rel = resolved.relative_to(workdir.resolve())
    except ValueError:
        raise SystemExit("output path must stay inside the LLL workdir")
    root = worker_root_rel(workdir).split("/")
    if len(rel.parts) < len(root) + 1 or list(rel.parts[:len(root)]) != root:
        raise SystemExit(f"output path must be under {worker_root_rel(workdir)}/<task-id>/")
    if task_id is not None and rel.parts[len(root)] != task_id:
        raise SystemExit(f"output path for {task_id} must be under {worker_root_rel(workdir)}/{task_id}/")
    return rel.as_posix().rstrip("/") + "/"


def event(workdir: Path, *, task_id: str | None, event_name: str, status: str = "info", message: str = "", artifacts: list[str] | None = None, carrier: str = "lll", actor: str = "lll", exit_code: int | None = None, duration_ms: int | None = None, run_id: str | None = None) -> dict[str, Any]:
    obj = {
        "ts": now(), "run_id": run_id or "R-" + uuid.uuid4().hex[:10], "task_id": task_id,
        "actor": actor, "carrier": carrier, "event": event_name, "status": status,
        "message": message, "artifacts": artifacts or [], "exit_code": exit_code, "duration_ms": duration_ms,
    }
    append_jsonl(runs_path(workdir), obj)
    return obj


def read_config(workdir: Path) -> dict[str, Any]:
    p = config_path(workdir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid config {p}: {e}")


def write_config(workdir: Path, cfg: dict[str, Any]) -> None:
    cfg.setdefault("schema", "lll.config.v1")
    cfg["updated_at"] = now()
    atomic_write(config_path(workdir), json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    return value.strip("-") or "task"


def next_task_id(workdir: Path) -> str:
    nums = []
    for t in read_jsonl(tasks_path(workdir)):
        tid = str(t.get("id", ""))
        m = re.fullmatch(r"T(\d+)", tid)
        if m:
            nums.append(int(m.group(1)))
    return f"T{(max(nums) + 1) if nums else 1:03d}"


def normalize_depends(values: list[str] | None) -> list[str]:
    out: list[str] = []
    seen = set()
    for v in values or []:
        for dep in str(v).split(","):
            dep = dep.strip()
            if dep and dep not in seen:
                out.append(dep)
                seen.add(dep)
    return out


def write_task_files(workdir: Path, task: dict[str, Any]) -> None:
    out = ensure_safe_relative_out(workdir, task.get("out") or default_task_out(workdir, task["id"]), task["id"])
    task["out"] = out
    td = workdir / out
    (td / "artifacts").mkdir(parents=True, exist_ok=True)
    task_md = f"""# LLL Worker Task

```text
task_id: {task['id']}
carrier: {task.get('carrier','lll')}
preset: {task.get('preset','manual')}
status: {task.get('status','pending')}
```

## Objective
{task.get('goal') or task.get('title')}

## Runner fields

- executor: `{task.get('executor','shell')}`
- command: `{task.get('command') or ''}`
- verify: `{task.get('verify_cmd') or ''}`
- repo: `{task.get('repo') or ''}`
- delivery: `{task.get('delivery','handoff')}`

## Required outputs

- [handoff.md](handoff.md)
- [artifacts/](artifacts/) as needed

## Compact LLL contract

Read `mission.md`, this task file, and listed inputs before starting. Keep detailed work under this task directory unless explicitly assigned a root human-facing deliverable. The runner/executor may propose completion, but verification and queue status decide final success.
"""
    if not (td / "task.md").exists():
        atomic_write(td / "task.md", task_md)
    if not (td / "status.json").exists():
        atomic_write(td / "status.json", json.dumps({"task_id": task["id"], "status": task.get("status", "pending"), "current_step": "queued", "attempts": task.get("attempts", 0), "outputs": [], "updated_at": now()}, indent=2, ensure_ascii=False) + "\n")
    if not (td / "log.txt").exists():
        atomic_write(td / "log.txt", f"{now()} task queued\n")
    if not (td / "handoff.md").exists():
        atomic_write(td / "handoff.md", f"# Worker Handoff\n\n```text\nstatus: {task.get('status','pending')}\ntask_id: {task['id']}\n```\n")


def update_local_status(workdir: Path, task: dict[str, Any], step: str = "") -> None:
    td = workdir / ensure_safe_relative_out(workdir, task.get("out") or default_task_out(workdir, task["id"]), task["id"])
    cur: dict[str, Any] = {}
    p = td / "status.json"
    if p.exists():
        try:
            cur = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cur = {}
    cur.update({
        "task_id": task["id"], "status": task.get("status"), "current_step": step or task.get("status"),
        "attempts": task.get("attempts", 0), "last_error": task.get("error"),
        "claim_id": task.get("claim_id"), "lease_until": task.get("lease_until"), "updated_at": now(),
    })
    atomic_write(p, json.dumps(cur, indent=2, ensure_ascii=False) + "\n")
    with (td / "log.txt").open("a", encoding="utf-8") as f:
        f.write(f"{now()} {task.get('status')} {step}\n")


@contextmanager
def queue_lock(workdir: Path, owner: str, ttl_seconds: int = 120) -> Iterator[None]:
    lock = state_dir(workdir) / "locks" / "tasks.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            lock.mkdir()
            atomic_write(lock / "owner.json", json.dumps({"owner": owner, "created_at": now(), "ttl_seconds": ttl_seconds}, indent=2) + "\n")
            break
        except FileExistsError:
            owner_path = lock / "owner.json"
            stale = False
            if owner_path.exists():
                try:
                    info = json.loads(owner_path.read_text(encoding="utf-8"))
                    created = parse_ts(info.get("created_at"))
                    stale = created is not None and datetime.now(created.tzinfo or UTC) - created > timedelta(seconds=int(info.get("ttl_seconds", ttl_seconds)))
                except Exception:
                    stale = True
            if stale:
                shutil.rmtree(lock, ignore_errors=True)
                continue
            raise SystemExit(f"queue locked: {lock}")
    try:
        yield
    finally:
        shutil.rmtree(lock, ignore_errors=True)


def load_tasks(workdir: Path) -> list[dict[str, Any]]:
    return read_jsonl(tasks_path(workdir))


def save_tasks(workdir: Path, tasks: list[dict[str, Any]]) -> None:
    write_jsonl_atomic(tasks_path(workdir), tasks)


def set_task_status(workdir: Path, task_id: str, status: str, *, note: str = "", error: str | None = None, claim_id: str | None = None) -> dict[str, Any]:
    if status not in VALID_STATUS:
        raise SystemExit(f"Invalid status: {status}")
    with queue_lock(workdir, "set-status"):
        tasks = load_tasks(workdir)
        found = None
        for t in tasks:
            if t.get("id") == task_id:
                if claim_id and t.get("claim_id") and t.get("claim_id") != claim_id:
                    raise SystemExit(f"claim mismatch for {task_id}")
                t["status"] = status
                t["updated_at"] = now()
                if error is not None:
                    t["error"] = error
                if status not in ACTIVE_STATUS:
                    t["lease_until"] = None
                    t["claim_id"] = None
                found = t
                break
        if found is None:
            raise SystemExit(f"No such task: {task_id}")
        save_tasks(workdir, tasks)
    update_local_status(workdir, found, note or status)
    event(workdir, task_id=task_id, event_name="status", status="ok", message=note or status, artifacts=[found.get("out", "") + "status.json"])
    return found


def cmd_init(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    existing_core = [name for name in ["mission.md", "internal/tasks.jsonl", "internal/runs.jsonl"] if (wd / name).exists()]
    if existing_core and not args.force:
        raise SystemExit("LLL workdir already initialized: " + ", ".join(existing_core) + ". Use --force to reinitialize.")
    for sub in ["internal/logs", "internal/agents", "internal/inputs", "internal/locks"]:
        (wd / sub).mkdir(parents=True, exist_ok=True)
    ts = now()
    mission = f"""# LLL Mission

```text
mission_id: {wd.name}
created_at: {ts}
updated_at: {ts}
status: initialized
```

## Objective
{args.objective or '<fill objective>'}

## Success criteria
- observable mission criteria are recorded here
- `lll validate` passes before final delivery
- human-facing deliverables live beside `mission.md`; process state lives under `internal/`

## Execution policy
- Plain files are the source of truth; the CLI is only a reference implementation.
- Runner tasks may execute commands, but verification and queue state decide completion.
- Do not put secrets into prompts, logs, commits, or reports.
"""
    atomic_write(wd / "mission.md", mission)
    for rel, text in {
        "internal/tasks.jsonl": "",
        "internal/runs.jsonl": "",
        "internal/agent-registry.md": "# Agent / Worker Registry\n\n| id | role | carrier | status | output |\n|---|---|---|---|---|\n| lll | CLI runner/reference implementation | local process | available | internal/agents/* |\n",
        "internal/validation-report.md": "# Validation Report\n\n```text\nverdict: pending\n```\n",
        "internal/handoff.md": "# Internal LLL Handoff\n\nstatus: initialized\n",
        "internal/recovery-state.md": f"# Recovery State\n\nlast_updated: {ts}\nstatus: initialized\nnext_action: add tasks or run the queue\n",
        "internal/logs/supervisor.log": f"{ts} initialized {wd}\n",
        "internal/logs/runner.log": "",
    }.items():
        atomic_write(wd / rel, text)
    append_jsonl(error_report_path(wd), {"ts": ts, "type": "init", "severity": "info", "what_happened": "LLL workdir initialized", "evidence": ["mission.md"], "impact": "none", "fix_or_fallback": "n/a", "self_maintenance": "n/a"})
    append_jsonl(traceability_path(wd), {"ts": ts, "type": "init", "item": "workdir", "evidence": ["mission.md"], "status": "supported", "notes": "LLL workdir initialized by lll CLI"})
    cfg = {"version": 1, "mode": "lll", "workdir": str(wd), "default_executor": "shell", "lease_ttl_seconds": args.lease_ttl, "repo": args.repo or None, "git": {"use_worktree": bool(args.repo), "branch_prefix": "agent-loop/", "delivery": "handoff", "commit_policy": "on_verified_success"}, "verify": {"default_cmd": args.verify or None}}
    write_config(wd, cfg)
    event(wd, task_id=None, event_name="workdir_created", status="ok", message="LLL workdir initialized", artifacts=["mission.md", "internal/lll-config.json"])
    if args.json:
        print(json.dumps({"workdir": str(wd), "config": str(config_path(wd))}, indent=2, ensure_ascii=False))
    else:
        print(wd)


def cmd_task_add(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    cfg = read_config(wd)
    tid = args.id or next_task_id(wd)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", tid):
        raise SystemExit("task id must contain only letters, numbers, dot, underscore, hyphen")
    with queue_lock(wd, "task-add"):
        tasks = load_tasks(wd)
        if any(t.get("id") == tid for t in tasks):
            raise SystemExit(f"Task already exists: {tid}")
        task = {
            "id": tid, "title": args.title, "status": "pending", "priority": args.priority,
            "depends_on": normalize_depends(args.depends_on), "carrier": "lll", "preset": args.preset,
            "attempts": 0, "max_attempts": args.max_attempts,
            "out": ensure_safe_relative_out(wd, args.out or default_task_out(wd, tid), tid),
            "goal": args.goal, "acceptance": args.acceptance or ["runner handoff written"],
            "inputs": args.inputs or ["mission.md"], "created_at": now(), "updated_at": now(),
            "claim_id": None, "lease_until": None, "error": None,
            "executor": args.executor, "command": args.command, "verify_cmd": args.verify or (cfg.get("verify") or {}).get("default_cmd"),
            "timeout_seconds": args.timeout, "lease_ttl_seconds": args.lease_ttl or cfg.get("lease_ttl_seconds", 7200),
            "repo": args.repo or cfg.get("repo"), "cwd": args.cwd,
            "use_worktree": args.use_worktree if args.use_worktree is not None else bool(args.repo or cfg.get("repo")),
            "delivery": args.delivery,
        }
        tasks.append(task)
        tasks.sort(key=lambda t: (-int(t.get("priority", 0)), str(t.get("id", ""))))
        save_tasks(wd, tasks)
    write_task_files(wd, task)
    event(wd, task_id=tid, event_name="queued", status="ok", message=args.title, artifacts=[task["out"] + "task.md"])
    if args.json:
        print(json.dumps(task, indent=2, ensure_ascii=False))
    else:
        print(f"added {tid} -> {task['out']}")


def cmd_task_list(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    tasks = load_tasks(wd)
    if not args.all:
        tasks = [t for t in tasks if t.get("status") not in {"done", "succeeded", "cancelled"}]
    if args.json:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
        return
    if not tasks:
        print("no tasks")
        return
    for t in tasks:
        print(f"{t.get('id')} [{t.get('status')}] p{t.get('priority')} {t.get('preset')} - {t.get('title')}")


def cmd_task_set_status(args: argparse.Namespace) -> None:
    task = set_task_status(Path(args.workdir).expanduser().resolve(), args.id, args.status, note=args.note, error=args.error)
    if args.json:
        print(json.dumps(task, indent=2, ensure_ascii=False))
    else:
        print(f"{args.id} -> {args.status}")


def status_summary(workdir: Path) -> dict[str, Any]:
    tasks = load_tasks(workdir)
    counts: dict[str, int] = {}
    for t in tasks:
        counts[str(t.get("status", "unknown"))] = counts.get(str(t.get("status", "unknown")), 0) + 1
    return {"workdir": str(workdir), "layout": layout_kind(workdir), "counts": counts, "tasks": tasks}


def cmd_status(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    summary = status_summary(wd)
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return
    print(f"workdir: {wd}")
    print(f"layout: {summary['layout']}")
    print("tasks:", ", ".join(f"{k}={v}" for k, v in sorted(summary["counts"].items())) or "none")
    for t in summary["tasks"]:
        if args.all or t.get("status") not in {"done", "succeeded", "cancelled"}:
            print(f"{t.get('id')} [{t.get('status')}] p{t.get('priority')} {t.get('executor','shell')}/{t.get('preset')} - {t.get('title')}")


def validate_workdir(workdir: Path, *, mode: str = "auto") -> tuple[bool, list[str]]:
    messages: list[str] = []
    ok = True
    if mode == "auto":
        mode = "full" if tasks_path(workdir).exists() else "lite"
    required = [workdir / "mission.md"]
    if mode != "lite":
        required.extend([tasks_path(workdir), runs_path(workdir), recovery_path(workdir), registry_path(workdir), handoff_path(workdir), validation_path(workdir), error_report_path(workdir), traceability_path(workdir)])
    for p in required:
        if not p.exists():
            ok = False
            messages.append(f"missing: {rel_to_workdir(workdir, p) if p.is_relative_to(workdir) else p}")
    for p in [tasks_path(workdir), runs_path(workdir), error_report_path(workdir), traceability_path(workdir)]:
        if p.exists():
            try:
                read_jsonl(p)
            except SystemExit as e:
                ok = False
                messages.append(str(e))
    for name in ["output", "00-index.md", "00_index.md", "99-next-steps.md", "99_next_steps.md", "Next Step.md", "Next Steps.md"]:
        if (workdir / name).exists():
            ok = False
            messages.append(f"obsolete current-layout surface exists: {name}")
    tasks = load_tasks(workdir) if tasks_path(workdir).exists() else []
    ids: set[str] = set()
    for t in tasks:
        tid = t.get("id")
        if not isinstance(tid, str) or not tid:
            ok = False; messages.append("task with missing/invalid id"); continue
        if tid in ids:
            ok = False; messages.append(f"duplicate task id {tid}")
        ids.add(tid)
        if t.get("status") not in VALID_STATUS:
            ok = False; messages.append(f"task {tid} has invalid status {t.get('status')}")
        for dep in t.get("depends_on", []) or []:
            if dep not in ids and dep not in [x.get("id") for x in tasks]:
                ok = False; messages.append(f"task {tid} has missing dependency {dep}")
        try:
            out = ensure_safe_relative_out(workdir, t.get("out") or default_task_out(workdir, tid), tid)
        except SystemExit as e:
            ok = False; messages.append(f"task {tid} invalid out path: {e}"); continue
        td = workdir / out
        for rel in ["task.md", "status.json", "log.txt", "handoff.md", "artifacts"]:
            if not (td / rel).exists():
                ok = False; messages.append(f"task {tid} missing {out}{rel}")
    return ok, messages


def cmd_validate(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    ok, messages = validate_workdir(wd, mode=args.mode)
    if args.json:
        print(json.dumps({"workdir": str(wd), "ok": ok, "messages": messages}, indent=2, ensure_ascii=False))
    else:
        if messages:
            print("\n".join(messages))
        if ok:
            print(f"LLL workdir structure valid ({layout_kind(wd)}, {args.mode})")
    raise SystemExit(0 if ok else 1)


def cmd_event(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    obj = event(wd, task_id=args.task_id, event_name=args.event, status=args.status, message=args.message, artifacts=args.artifact or [], carrier=args.carrier, actor=args.actor)
    if args.json:
        print(json.dumps({"schema": "lll.event.v1", "ok": True, "workdir": str(wd), "event": obj}, indent=2, ensure_ascii=False))
    else:
        print("event appended")


def cmd_checkpoint(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    tasks = load_tasks(wd)
    active = [t["id"] for t in tasks if t.get("status") in ACTIVE_STATUS]
    blocked = [t["id"] for t in tasks if t.get("status") == "blocked"]
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
"""
    atomic_write(recovery_path(wd), text)
    obj = event(wd, task_id=None, event_name="checkpoint", status="ok", message=args.checkpoint, artifacts=[rel_to_workdir(wd, recovery_path(wd))])
    report = {"schema": "lll.checkpoint.v1", "ok": True, "workdir": str(wd), "recovery_state": str(recovery_path(wd)), "active_tasks": active, "blocked_tasks": blocked, "event": obj}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("checkpoint updated")


def claim_next(workdir: Path, owner: str) -> dict[str, Any] | None:
    with queue_lock(workdir, owner):
        tasks = load_tasks(workdir)
        ids_done = {t.get("id") for t in tasks if t.get("status") in {"done", "succeeded"}}
        for t in tasks:
            if t.get("status") not in CLAIMABLE_STATUS:
                continue
            if any(dep not in ids_done for dep in t.get("depends_on", []) or []):
                continue
            lease_seconds = int(t.get("lease_ttl_seconds") or read_config(workdir).get("lease_ttl_seconds", 7200))
            t["status"] = "leased"
            t["claim_id"] = owner + ":" + uuid.uuid4().hex[:10]
            t["lease_until"] = (datetime.now().astimezone() + timedelta(seconds=lease_seconds)).isoformat(timespec="seconds")
            t["updated_at"] = now()
            t["attempts"] = int(t.get("attempts", 0)) + 1
            save_tasks(workdir, tasks)
            update_local_status(workdir, t, "claimed")
            event(workdir, task_id=t["id"], event_name="claimed", status="ok", message=owner)
            return t
    return None


def update_task(workdir: Path, task: dict[str, Any], *, status: str, step: str = "", error: str | None = None) -> dict[str, Any]:
    with queue_lock(workdir, "runner-update"):
        tasks = load_tasks(workdir)
        saved = None
        for t in tasks:
            if t.get("id") == task.get("id"):
                t.update(task)
                t["status"] = status
                t["updated_at"] = now()
                if error is not None:
                    t["error"] = error
                if status not in ACTIVE_STATUS:
                    t["claim_id"] = None
                    t["lease_until"] = None
                saved = t
                break
        if saved is None:
            raise SystemExit(f"No such task: {task.get('id')}")
        save_tasks(workdir, tasks)
    update_local_status(workdir, saved, step or status)
    return saved


def run_cmd(cmd: str, *, cwd: Path, stdout: Path, stderr: Path, timeout: int) -> tuple[int, bool, int]:
    start = time.monotonic()
    stdout.parent.mkdir(parents=True, exist_ok=True)
    with stdout.open("w", encoding="utf-8", errors="replace") as out, stderr.open("w", encoding="utf-8", errors="replace") as err:
        if os.name == "nt":
            proc = subprocess.Popen(cmd, cwd=str(cwd), shell=True, stdout=out, stderr=err, creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        else:
            proc = subprocess.Popen(cmd, cwd=str(cwd), shell=True, stdout=out, stderr=err, start_new_session=True)
        try:
            rc = proc.wait(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
            if os.name == "nt":
                proc.terminate()
            else:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            try:
                rc = proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if os.name != "nt":
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                rc = proc.wait()
    return int(rc), timed_out, int((time.monotonic() - start) * 1000)


def git_output(args: list[str], cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=str(cwd), text=True, stderr=subprocess.STDOUT).strip()


def prepare_cwd(workdir: Path, task: dict[str, Any]) -> tuple[Path, str | None]:
    td = workdir / ensure_safe_relative_out(workdir, task.get("out") or default_task_out(workdir, task["id"]), task["id"])
    repo_raw = task.get("repo")
    if task.get("cwd"):
        cwd = Path(str(task["cwd"])).expanduser().resolve()
        if not cwd.exists():
            raise SystemExit(f"cwd missing: {cwd}")
        return cwd, None
    if repo_raw:
        repo = Path(str(repo_raw)).expanduser().resolve()
        if task.get("use_worktree", True):
            if git_output(["status", "--porcelain"], repo):
                raise SystemExit(f"repo is dirty; refusing worktree run: {repo}")
            branch = f"agent-loop/{task['id']}-attempt-{task.get('attempts', 1)}"
            wt = state_dir(workdir) / "worktrees" / task["id"]
            if not wt.exists():
                wt.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "-C", str(repo), "worktree", "add", "-B", branch, str(wt), "HEAD"], check=True)
            task["worktree"] = str(wt)
            task["branch"] = branch
            return wt.resolve(), branch
        return repo, None
    return td.resolve(), None


def write_prompt(workdir: Path, task: dict[str, Any], run_dir: Path, cwd: Path) -> Path:
    prompt = run_dir / "prompt.md"
    text = f"""# LLL Runner Prompt

Task: {task['id']} — {task.get('title')}

Goal:
{task.get('goal')}

Command executor: {task.get('executor','shell')}
Command:
```sh
{task.get('command') or ''}
```

Working directory: `{cwd}`

Acceptance:
{chr(10).join('- ' + str(x) for x in (task.get('acceptance') or []))}
"""
    atomic_write(prompt, text)
    return prompt


def finish_handoff(workdir: Path, task: dict[str, Any], run_dir: Path, status: str, rc: int, verify_rc: int | None, message: str) -> None:
    td = workdir / ensure_safe_relative_out(workdir, task.get("out") or default_task_out(workdir, task["id"]), task["id"])
    rel_run = rel_to_workdir(workdir, run_dir)
    text = f"""# Worker Handoff

```text
status: {status}
task_id: {task['id']}
run: {rel_run}
```

## Result

- executor_exit_code: `{rc}`
- verify_exit_code: `{verify_rc if verify_rc is not None else 'not-run'}`
- message: {message}

## Artifacts

- [{rel_run}/prompt.md](../../../{rel_run}/prompt.md)
- [{rel_run}/stdout.log](../../../{rel_run}/stdout.log)
- [{rel_run}/stderr.log](../../../{rel_run}/stderr.log)
- [{rel_run}/verify.log](../../../{rel_run}/verify.log)
- [{rel_run}/result.json](../../../{rel_run}/result.json)
"""
    atomic_write(td / "handoff.md", text)


def maybe_commit(task: dict[str, Any], cwd: Path) -> str | None:
    if task.get("delivery") != "local-commit" or not (cwd / ".git").exists() and not (cwd / ".git").is_file():
        return None
    if not git_output(["status", "--porcelain"], cwd):
        return None
    subprocess.run(["git", "add", "-A"], cwd=str(cwd), check=True)
    title = str(task.get("title") or task["id"]).replace("\n", " ")[:72]
    subprocess.run(["git", "commit", "-m", f"agent-loop: {title}"], cwd=str(cwd), check=True)
    return git_output(["rev-parse", "--short", "HEAD"], cwd)


def run_once(workdir: Path, *, owner: str | None = None) -> tuple[int, dict[str, Any]]:
    owner = owner or f"lll-{os.getpid()}"
    task = claim_next(workdir, owner)
    if not task:
        report = {"schema": "lll.run.once.v1", "ok": True, "workdir": str(workdir), "owner": owner, "claimed": False, "message": "no claimable task", "exit_code": 0}
        return 0, report
    run_id = "runner-run-" + datetime.now().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]
    td = workdir / ensure_safe_relative_out(workdir, task.get("out") or default_task_out(workdir, task["id"]), task["id"])
    run_dir = td / "artifacts" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    task = update_task(workdir, task, status="running", step="executor starting")
    try:
        cwd, branch = prepare_cwd(workdir, task)
        prompt = write_prompt(workdir, task, run_dir, cwd)
        cmd = task.get("command")
        if not cmd:
            raise SystemExit(f"task {task['id']} has no shell command; write handoff manually or enqueue with --command")
        event(workdir, task_id=task["id"], event_name="executor_started", status="ok", message=cmd, artifacts=[rel_to_workdir(workdir, prompt)], run_id=run_id)
        rc, timed_out, duration = run_cmd(str(cmd), cwd=cwd, stdout=run_dir / "stdout.log", stderr=run_dir / "stderr.log", timeout=int(task.get("timeout_seconds") or 3600))
        event(workdir, task_id=task["id"], event_name="executor_exit", status="ok" if rc == 0 and not timed_out else "error", message="timeout" if timed_out else "completed", artifacts=[rel_to_workdir(workdir, run_dir / "stdout.log"), rel_to_workdir(workdir, run_dir / "stderr.log")], exit_code=rc, duration_ms=duration, run_id=run_id)
        verify_rc: int | None = None
        if rc == 0 and not timed_out and task.get("verify_cmd"):
            task = update_task(workdir, task, status="verifying", step=str(task.get("verify_cmd")))
            verify_rc, _, verify_ms = run_cmd(str(task["verify_cmd"]), cwd=cwd, stdout=run_dir / "verify.log", stderr=run_dir / "verify.log.stderr", timeout=int(task.get("timeout_seconds") or 3600))
            event(workdir, task_id=task["id"], event_name="verify_exit", status="ok" if verify_rc == 0 else "error", message=str(task.get("verify_cmd")), artifacts=[rel_to_workdir(workdir, run_dir / "verify.log")], exit_code=verify_rc, duration_ms=verify_ms, run_id=run_id)
        success = rc == 0 and not timed_out and (verify_rc in {None, 0})
        commit = maybe_commit(task, cwd) if success else None
        result_status = "succeeded" if success else ("failed_retryable" if int(task.get("attempts", 0)) < int(task.get("max_attempts", 1)) else "failed_terminal")
        result = {"run_id": run_id, "task_id": task["id"], "status": result_status, "exit_code": rc, "timed_out": timed_out, "verify_exit_code": verify_rc, "cwd": str(cwd), "branch": branch, "commit": commit, "updated_at": now()}
        result_path = run_dir / "result.json"
        atomic_write(result_path, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        finish_handoff(workdir, task, run_dir, result_status, rc, verify_rc, "verified" if success else "failed")
        task = update_task(workdir, task, status=result_status, step="runner completed", error=None if success else f"exit={rc} verify={verify_rc} timeout={timed_out}")
        finish_event = event(workdir, task_id=task["id"], event_name="task_finished", status="ok" if success else "error", message=result_status, artifacts=[rel_to_workdir(workdir, result_path), task.get("out", "") + "handoff.md"], exit_code=0 if success else rc, run_id=run_id)
        exit_code = 0 if success else 1
        report = {"schema": "lll.run.once.v1", "ok": success, "workdir": str(workdir), "owner": owner, "claimed": True, "task_id": task["id"], "run_id": run_id, "status": result_status, "result": result, "result_path": str(result_path), "handoff": str(td / "handoff.md"), "event": finish_event, "exit_code": exit_code}
        return exit_code, report
    except BaseException as e:
        result_status = "failed_retryable" if int(task.get("attempts", 0)) < int(task.get("max_attempts", 1)) else "failed_terminal"
        result = {"run_id": run_id, "task_id": task["id"], "status": result_status, "error": str(e), "updated_at": now()}
        result_path = run_dir / "result.json"
        atomic_write(result_path, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        finish_handoff(workdir, task, run_dir, result_status, 1, None, str(e))
        update_task(workdir, task, status=result_status, step="runner exception", error=str(e))
        err_event = event(workdir, task_id=task["id"], event_name="runner_exception", status="error", message=str(e), artifacts=[rel_to_workdir(workdir, result_path)], exit_code=1, run_id=run_id)
        print(f"runner error: {e}", file=sys.stderr)
        return 1, {"schema": "lll.run.once.v1", "ok": False, "workdir": str(workdir), "owner": owner, "claimed": True, "task_id": task["id"], "run_id": run_id, "status": result_status, "result": result, "result_path": str(result_path), "handoff": str(td / "handoff.md"), "event": err_event, "exit_code": 1}


def cmd_run_once(args: argparse.Namespace) -> None:
    rc, report = run_once(Path(args.workdir).expanduser().resolve(), owner=args.owner)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif not report.get("claimed"):
        print(report.get("message", "no claimable task"))
    raise SystemExit(rc)


def cmd_run_serve(args: argparse.Namespace) -> None:
    if args.max_concurrent != 1:
        raise SystemExit("POC serve supports --max-concurrent 1 only")
    wd = Path(args.workdir).expanduser().resolve()
    i = 0
    reports: list[dict[str, Any]] = []
    rc = 0
    while True:
        rc, report = run_once(wd, owner=args.owner or f"lll-serve-{os.getpid()}")
        reports.append(report)
        if not args.json and not report.get("claimed"):
            print(report.get("message", "no claimable task"))
        i += 1
        if args.max_iterations and i >= args.max_iterations:
            if args.json:
                print(json.dumps({"schema": "lll.run.serve.v1", "ok": rc == 0, "workdir": str(wd), "iterations": i, "runs": reports, "exit_code": rc}, indent=2, ensure_ascii=False))
            raise SystemExit(rc)
        time.sleep(args.interval)


def cmd_run_reaper(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    now_dt = datetime.now().astimezone()
    changed: list[str] = []
    with queue_lock(wd, "reaper"):
        tasks = load_tasks(wd)
        for t in tasks:
            if t.get("status") not in ACTIVE_STATUS:
                continue
            lease = parse_ts(t.get("lease_until"))
            if lease and lease < now_dt:
                t["status"] = "failed_retryable" if int(t.get("attempts", 0)) < int(t.get("max_attempts", 1)) else "failed_terminal"
                t["error"] = "lease expired and was reaped"
                t["claim_id"] = None
                t["lease_until"] = None
                t["updated_at"] = now()
                changed.append(t["id"])
        save_tasks(wd, tasks)
    events = []
    for tid in changed:
        task = next(t for t in load_tasks(wd) if t.get("id") == tid)
        update_local_status(wd, task, "reaped expired lease")
        events.append(event(wd, task_id=tid, event_name="reaped", status="warning", message="expired lease"))
    report = {"schema": "lll.run.reaper.v1", "ok": True, "workdir": str(wd), "reaped": changed, "count": len(changed), "events": events}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"reaped: {len(changed)}" + (" " + ", ".join(changed) if changed else ""))


def render_service(target: str, *, name: str, runner_bin: str, workdir: Path, interval: int) -> dict[str, str]:
    if target == "systemd":
        service = f"""[Unit]
Description=LLL Runner - {name}
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={workdir}
ExecStart={runner_bin} run serve {workdir} --interval {interval}
Restart=on-failure
RestartSec=15s
KillMode=control-group
TimeoutStopSec=60

[Install]
WantedBy=default.target
"""
        reaper_service = f"""[Unit]
Description=LLL Runner Reaper - {name}

[Service]
Type=oneshot
WorkingDirectory={workdir}
ExecStart={runner_bin} run reaper {workdir}
"""
        timer = f"""[Unit]
Description=LLL Runner Reaper Timer - {name}

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
"""
        return {f"lll-{name}.service": service, f"lll-{name}-reaper.service": reaper_service, f"lll-{name}-reaper.timer": timer}
    if target == "launchd":
        plist = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\"><dict>
  <key>Label</key><string>com.lin.lll.{name}</string>
  <key>ProgramArguments</key><array><string>{runner_bin}</string><string>run</string><string>serve</string><string>{workdir}</string><string>--interval</string><string>{interval}</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>{workdir}/internal/logs/runner.stdout.log</string>
  <key>StandardErrorPath</key><string>{workdir}/internal/logs/runner.stderr.log</string>
</dict></plist>
"""
        return {f"com.lin.lll.{name}.plist": plist}
    if target == "windows-task":
        ps1 = f"""$Action = New-ScheduledTaskAction -Execute \"{runner_bin}\" -Argument \"run serve {workdir.as_posix()} --interval {interval}\"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 0)
Register-ScheduledTask -TaskName \"LLLRunner-{name}\" -Action $Action -Trigger $Trigger -Settings $Settings -Description \"LLL Runner\"
"""
        return {f"install-windows-task-{name}.ps1": ps1}
    raise SystemExit(f"unknown service target: {target}")


def cmd_service_install(args: argparse.Namespace) -> None:
    wd = Path(args.workdir).expanduser().resolve()
    name = slugify(args.name or wd.name)[:48]
    runner_bin = args.runner_bin or shutil.which("lll") or str(Path(__file__).resolve().parents[2] / "lll")
    files = render_service(args.target, name=name, runner_bin=runner_bin, workdir=wd, interval=args.interval)
    out_dir = state_dir(wd) / "service"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for filename, text in files.items():
        p = out_dir / filename
        atomic_write(p, text)
        written.append(str(p))
    if args.apply and args.target == "systemd":
        user_dir = Path.home() / ".config" / "systemd" / "user"
        user_dir.mkdir(parents=True, exist_ok=True)
        for p in written:
            shutil.copy2(p, user_dir / Path(p).name)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        if not args.no_enable:
            subprocess.run(["systemctl", "--user", "enable", "--now", f"lll-{name}.service"], check=False)
    if args.json:
        print(json.dumps({"schema": "lll.service.install.v1", "ok": True, "workdir": str(wd), "target": args.target, "name": name, "apply": bool(args.apply), "files": written}, indent=2, ensure_ascii=False))
    else:
        print("generated service files:")
        for p in written:
            print(p)


def cmd_list_workdirs(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser().resolve()
    rows = []
    if root.exists():
        for p in sorted([x for x in root.iterdir() if x.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True):
            markers = [m for m in ["mission.md", "internal/tasks.jsonl", "internal/recovery-state.md", "tasks.jsonl"] if (p / m).exists()]
            if markers or args.all:
                rows.append({"name": p.name, "path": str(p), "is_lll": bool(markers), "markers": markers, "mtime": datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat(timespec="seconds")})
            if args.limit and len(rows) >= args.limit:
                break
    if args.json:
        print(json.dumps({"root": str(root), "workdirs": rows}, indent=2, ensure_ascii=False))
    else:
        for r in rows:
            print(f"- {r['name']} [{'lll' if r['is_lll'] else 'dir'}] {r['path']}")


def cmd_doctor(args: argparse.Namespace) -> None:
    """Emit a compact readiness report for agents and install scripts."""
    root = Path(args.root).expanduser().resolve()
    executable = Path(sys.argv[0]).expanduser()
    source_dir = Path(__file__).resolve().parents[2]
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    check("python", sys.version_info >= (3, 11), sys.version.split()[0])
    check("source_dir", source_dir.exists(), str(source_dir))
    if args.create_root:
        root.mkdir(parents=True, exist_ok=True)
    root_ready = root.exists() or root.parent.exists()
    root_detail = str(root) if root.exists() else f"{root} (will be created by init/run commands)"
    check("work_root", root_ready, root_detail)
    if args.workdir:
        wd = Path(args.workdir).expanduser().resolve()
        check("workdir", wd.exists(), str(wd))
        if wd.exists():
            valid, messages = validate_workdir(wd, mode=args.mode)
            check("workdir_validate", valid, "; ".join(messages[:5]) if messages and not valid else f"valid ({layout_kind(wd)}, {args.mode})")
    report = {
        "schema": "lll.doctor.v1",
        "ok": all(c["ok"] for c in checks),
        "version": __version__,
        "executable": str(executable),
        "source_dir": str(source_dir),
        "default_root": str(root),
        "checks": checks,
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"lll {__version__}")
        for c in checks:
            print(f"{c['name']}: {'ok' if c['ok'] else 'missing'} - {c['detail']}")
    raise SystemExit(0 if report["ok"] else 1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lll", description="Lin's Living Loop CLI reference implementation", epilog=f"Recommended new workdir pattern: {RECOMMENDED_WORKDIR_PATTERN}")
    p.add_argument("--version", action="version", version=f"lll {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create a LLL workdir")
    s.add_argument("workdir"); s.add_argument("--objective", default=""); s.add_argument("--repo"); s.add_argument("--verify", default=""); s.add_argument("--lease-ttl", type=int, default=7200); s.add_argument("--force", action="store_true"); s.add_argument("--json", action="store_true"); s.set_defaults(func=cmd_init)

    task = sub.add_parser("task", help="manage tasks")
    tsub = task.add_subparsers(dest="task_cmd", required=True)
    a = tsub.add_parser("add", help="add a task")
    a.add_argument("workdir"); a.add_argument("--id"); a.add_argument("--title", required=True); a.add_argument("--goal", required=True); a.add_argument("--preset", default="manual"); a.add_argument("--priority", type=int, default=10); a.add_argument("--depends-on", action="append", default=[]); a.add_argument("--acceptance", action="append", default=[]); a.add_argument("--inputs", action="append", default=[]); a.add_argument("--executor", default="shell", choices=["shell"]); a.add_argument("--command"); a.add_argument("--verify"); a.add_argument("--timeout", type=int, default=3600); a.add_argument("--lease-ttl", type=int); a.add_argument("--max-attempts", type=int, default=2); a.add_argument("--repo"); a.add_argument("--cwd"); a.add_argument("--use-worktree", dest="use_worktree", action="store_true", default=None); a.add_argument("--no-worktree", dest="use_worktree", action="store_false"); a.add_argument("--delivery", choices=["handoff", "local-commit"], default="handoff"); a.add_argument("--out", default=""); a.add_argument("--json", action="store_true"); a.set_defaults(func=cmd_task_add)
    l = tsub.add_parser("list", help="list tasks"); l.add_argument("workdir"); l.add_argument("--all", action="store_true"); l.add_argument("--json", action="store_true"); l.set_defaults(func=cmd_task_list)
    ss = tsub.add_parser("set-status", help="set task status"); ss.add_argument("workdir"); ss.add_argument("id"); ss.add_argument("status"); ss.add_argument("--note", default=""); ss.add_argument("--error"); ss.add_argument("--json", action="store_true"); ss.set_defaults(func=cmd_task_set_status)

    s = sub.add_parser("status", help="show workdir status"); s.add_argument("workdir"); s.add_argument("--all", action="store_true"); s.add_argument("--json", action="store_true"); s.set_defaults(func=cmd_status)
    s = sub.add_parser("validate", help="validate a workdir"); s.add_argument("workdir"); s.add_argument("--mode", choices=["auto", "full", "lite"], default="auto"); s.add_argument("--json", action="store_true"); s.set_defaults(func=cmd_validate)
    s = sub.add_parser("event", help="append an event"); s.add_argument("workdir"); s.add_argument("--task-id"); s.add_argument("--event", required=True); s.add_argument("--status", default="info"); s.add_argument("--message", default=""); s.add_argument("--artifact", action="append", default=[]); s.add_argument("--carrier", default="lll"); s.add_argument("--actor", default="lll"); s.add_argument("--json", action="store_true"); s.set_defaults(func=cmd_event)
    s = sub.add_parser("checkpoint", help="rewrite recovery-state.md"); s.add_argument("workdir"); s.add_argument("--status", default="active"); s.add_argument("--phase", default="working"); s.add_argument("--checkpoint", default="manual_checkpoint"); s.add_argument("--next-action", default="continue next task"); s.add_argument("--running", default=""); s.add_argument("--json", action="store_true"); s.set_defaults(func=cmd_checkpoint)

    r = sub.add_parser("run", help="runner commands")
    rsub = r.add_subparsers(dest="run_cmd", required=True)
    ro = rsub.add_parser("once", help="claim and run one task"); ro.add_argument("workdir"); ro.add_argument("--owner"); ro.add_argument("--json", action="store_true"); ro.set_defaults(func=cmd_run_once)
    rs = rsub.add_parser("serve", help="loop over run once"); rs.add_argument("workdir"); rs.add_argument("--interval", type=int, default=300); rs.add_argument("--max-concurrent", type=int, default=1); rs.add_argument("--max-iterations", type=int, default=0); rs.add_argument("--owner"); rs.add_argument("--json", action="store_true"); rs.set_defaults(func=cmd_run_serve)
    rr = rsub.add_parser("reaper", help="reap expired leases"); rr.add_argument("workdir"); rr.add_argument("--json", action="store_true"); rr.set_defaults(func=cmd_run_reaper)

    sv = sub.add_parser("service", help="generate service wrappers")
    svsub = sv.add_subparsers(dest="service_cmd", required=True)
    si = svsub.add_parser("install", help="generate/install service wrapper"); si.add_argument("workdir"); si.add_argument("--target", required=True, choices=["systemd", "launchd", "windows-task"]); si.add_argument("--user", action="store_true"); si.add_argument("--name"); si.add_argument("--interval", type=int, default=300); si.add_argument("--runner-bin"); si.add_argument("--apply", action="store_true"); si.add_argument("--no-enable", action="store_true"); si.add_argument("--json", action="store_true"); si.set_defaults(func=cmd_service_install)

    lw = sub.add_parser("list", help="list probable LLL workdirs under a root"); lw.add_argument("--root", default="~/lll-work"); lw.add_argument("--all", action="store_true"); lw.add_argument("--limit", type=int, default=50); lw.add_argument("--json", action="store_true"); lw.set_defaults(func=cmd_list_workdirs)
    d = sub.add_parser("doctor", help="check CLI readiness and optionally validate a workdir"); d.add_argument("workdir", nargs="?"); d.add_argument("--root", default="~/lll-work"); d.add_argument("--mode", choices=["auto", "full", "lite"], default="auto"); d.add_argument("--create-root", action="store_true"); d.add_argument("--json", action="store_true"); d.set_defaults(func=cmd_doctor)

    # Backward-compatible flat helper commands.
    a = sub.add_parser("add-task", help=argparse.SUPPRESS); a.add_argument("workdir"); a.add_argument("--id"); a.add_argument("--title", required=True); a.add_argument("--goal", required=True); a.add_argument("--carrier", default="lll"); a.add_argument("--preset", default="manual"); a.add_argument("--priority", type=int, default=10); a.add_argument("--depends-on", action="append", default=[]); a.add_argument("--acceptance", action="append", default=[]); a.add_argument("--inputs", action="append", default=[]); a.add_argument("--max-attempts", type=int, default=2); a.add_argument("--out", default=""); a.set_defaults(func=lambda x: cmd_task_add(argparse.Namespace(**{**vars(x), "executor": "shell", "command": None, "verify": None, "timeout": 3600, "lease_ttl": None, "repo": None, "cwd": None, "use_worktree": None, "delivery": "handoff", "json": False})))
    ss = sub.add_parser("set-status", help=argparse.SUPPRESS); ss.add_argument("workdir"); ss.add_argument("id"); ss.add_argument("status"); ss.add_argument("--note", default=""); ss.add_argument("--error"); ss.set_defaults(func=lambda x: cmd_task_set_status(argparse.Namespace(**{**vars(x), "json": False})))
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
