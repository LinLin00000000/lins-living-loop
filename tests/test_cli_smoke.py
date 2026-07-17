from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src") + (":" + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")}


def run(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run([sys.executable, "-m", "lll_cli", *args], cwd=str(cwd or ROOT), env=ENV, text=True, capture_output=True)
    if check and cp.returncode != 0:
        raise AssertionError(f"command failed {args}:\nSTDOUT={cp.stdout}\nSTDERR={cp.stderr}")
    return cp


class LLLCliSmokeTests(unittest.TestCase):
    def test_help_version_and_doctor(self) -> None:
        cp = run("--help")
        self.assertIn("init", cp.stdout)
        self.assertIn("run", cp.stdout)
        self.assertIn("doctor", cp.stdout)
        self.assertRegex(run("--version").stdout.strip(), r"^lll \d+\.\d+\.\d+")
        data = json.loads(run("doctor", "--json", "--root", str(ROOT)).stdout)
        self.assertEqual(data["schema"], "lll.doctor.v1")
        self.assertTrue(data["ok"])
        self.assertTrue(data["capabilities"]["json_envelope"])
        self.assertIn("task.add", data["capabilities"]["commands"])
        self.assertTrue(data["capabilities"]["workdir"]["name_validation"])
        self.assertEqual(data["capabilities"]["workdir"]["state_formats"]["singleton_snapshots"], "json")
        self.assertIn("internal/recovery.json", data["capabilities"]["workdir"]["canonical_state"])
        self.assertEqual(data["capabilities"]["runner"]["queue_lock_wait_seconds"], 5)

    def test_init_task_validate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "work"
            init_report = json.loads(run("init", str(wd), "--objective", "smoke", "--json").stdout)
            self.assertEqual(init_report["schema"], "lll.init.v1")
            self.assertTrue(init_report["ok"])
            recovery = json.loads((wd / "internal" / "recovery.json").read_text(encoding="utf-8"))
            validation = json.loads((wd / "internal" / "validation.json").read_text(encoding="utf-8"))
            self.assertEqual(recovery["schema"], "lll.recovery.v1")
            self.assertEqual(validation["schema"], "lll.validation.v1")
            self.assertFalse((wd / "internal" / "recovery-state.md").exists())
            self.assertFalse((wd / "internal" / "validation-report.md").exists())
            self.assertFalse((wd / "internal" / "agent-registry.md").exists())
            self.assertFalse((wd / "internal" / "handoff.md").exists())
            add_report = json.loads(run("task", "add", str(wd), "--title", "demo", "--goal", "write marker", "--command", "printf ok > marker.txt", "--verify", "test -f marker.txt", "--max-attempts", "1", "--json").stdout)
            self.assertEqual(add_report["schema"], "lll.task.add.v1")
            self.assertEqual(add_report["task"]["id"], "T001")
            cp = run("status", str(wd), "--json", "--compact")
            data = json.loads(cp.stdout)
            self.assertEqual(data["schema"], "lll.status.v1")
            self.assertEqual(data["counts"].get("pending"), 1)
            self.assertNotIn("tasks", data)
            self.assertEqual(data["active_tasks"][0]["id"], "T001")
            self.assertEqual(data["recovery"]["schema"], "lll.recovery.v1")
            self.assertEqual(data["validation"]["verdict"], "pending")
            validate_report = json.loads(run("validate", str(wd), "--json").stdout)
            self.assertEqual(validate_report["schema"], "lll.validate.v1")
            self.assertTrue(validate_report["ok"])
            self.assertFalse(validate_report["name"]["ok"])
            rc = run("run", "once", str(wd), "--json")
            self.assertEqual(rc.returncode, 0)
            run_report = json.loads(rc.stdout)
            self.assertEqual(run_report["schema"], "lll.run.once.v1")
            self.assertTrue(run_report["ok"])
            self.assertTrue(run_report["claimed"])
            self.assertEqual(run_report["status"], "succeeded")
            data = json.loads(run("status", str(wd), "--json").stdout)
            self.assertEqual(data["counts"].get("succeeded"), 1)
            artifacts = list((wd / "internal" / "agents" / "T001" / "artifacts").glob("runner-run-*/result.json"))
            self.assertTrue(artifacts)
            event_report = json.loads(run("event", str(wd), "--event", "note", "--message", "json", "--json").stdout)
            self.assertEqual(event_report["schema"], "lll.event.v1")
            checkpoint_report = json.loads(run("checkpoint", str(wd), "--checkpoint", "smoke", "--data", '{"notes":["preserved extension"],"current_phase":"stale","nonterminal_tasks":["ghost"]}', "--resume-order", "mission.md", "--resume-order", "internal/recovery.json", "--json").stdout)
            self.assertEqual(checkpoint_report["schema"], "lll.checkpoint.v1")
            recovery = json.loads((wd / "internal" / "recovery.json").read_text(encoding="utf-8"))
            self.assertEqual(recovery["checkpoint"], "smoke")
            self.assertEqual(recovery["resume_order"], ["mission.md", "internal/recovery.json"])
            self.assertEqual(recovery["notes"], ["preserved extension"])
            self.assertNotIn("current_phase", recovery)
            self.assertNotIn("nonterminal_tasks", recovery)

    def test_task_mutations_refresh_recovery_queue_summary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "20260711-180000_recovery-queue"
            run("init", str(wd), "--objective", "queue recovery consistency")
            run("checkpoint", str(wd), "--checkpoint", "before enqueue", "--json")

            run("task", "add", str(wd), "--id", "T001", "--title", "queued after checkpoint", "--goal", "prove queue visibility")
            queued = json.loads((wd / "internal" / "recovery.json").read_text(encoding="utf-8"))
            self.assertEqual(queued["operational_queue"]["tasks_path"], "internal/tasks.jsonl")
            self.assertEqual(queued["operational_queue"]["runs_path"], "internal/runs.jsonl")
            self.assertEqual(queued["operational_queue"]["nonterminal_count"], 1)
            self.assertEqual(queued["operational_queue"]["observed_through"], queued["updated_at"])

            run("task", "set-status", str(wd), "T001", "in_progress")
            active = json.loads((wd / "internal" / "recovery.json").read_text(encoding="utf-8"))
            self.assertEqual(active["active_tasks"], ["T001"])
            self.assertEqual(active["operational_queue"]["nonterminal_count"], 1)
            active["nonterminal_tasks"] = ["T001"]
            (wd / "internal" / "recovery.json").write_text(json.dumps(active), encoding="utf-8")

            run("task", "set-status", str(wd), "T001", "completed")
            completed = json.loads((wd / "internal" / "recovery.json").read_text(encoding="utf-8"))
            self.assertEqual(completed["active_tasks"], [])
            self.assertEqual(completed["operational_queue"]["nonterminal_count"], 0)
            self.assertNotIn("nonterminal_tasks", completed)

    def test_closeout_blocks_conflicting_legacy_recovery_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "20260717-184000_recovery-alias-drift"
            run("init", str(wd), "--objective", "detect stale recovery aliases")
            run("validation", "set", str(wd), "--verdict", "PASS", "--scope", "alias drift", "--summary", "fixture", "--validator", "unittest")
            recovery_path = wd / "internal" / "recovery.json"
            recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
            recovery["current_phase"] = "stale-phase"
            recovery["nonterminal_tasks"] = ["ghost"]
            recovery_path.write_text(json.dumps(recovery), encoding="utf-8")
            cp = run("closeout", str(wd), "--json", check=False)
            self.assertNotEqual(cp.returncode, 0)
            report = json.loads(cp.stdout)
            self.assertIn("recovery legacy field nonterminal_tasks conflicts with internal/tasks.jsonl", report["blocking"])
            self.assertIn("recovery legacy field current_phase conflicts with canonical phase", report["blocking"])

    def test_queue_lock_waits_for_short_contention(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "20260711-190000_queue-contention"
            run("init", str(wd), "--objective", "short lock contention")
            release_path = wd / "release-holder"
            holder_code = (
                "import time; from pathlib import Path; "
                "from lll_cli.main import queue_lock; "
                f"wd=Path({str(wd)!r}); release=Path({str(release_path)!r}); "
                "lock=queue_lock(wd, 'test-holder'); lock.__enter__(); "
                "\nwhile not release.exists(): time.sleep(0.01)\n"
                "lock.__exit__(None, None, None)"
            )
            holder = subprocess.Popen([sys.executable, "-c", holder_code], cwd=str(ROOT), env=ENV)
            owner_path = wd / "internal" / "locks" / "tasks.lock" / "owner.json"
            deadline = time.monotonic() + 2
            while not owner_path.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(owner_path.exists(), "lock holder did not become ready")

            waiter = subprocess.Popen(
                [sys.executable, "-m", "lll_cli", "task", "add", str(wd), "--title", "waiter", "--goal", "wait for lock"],
                cwd=str(ROOT), env=ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            try:
                time.sleep(0.1)
                blocked = waiter.poll() is None
            finally:
                release_path.write_text("release\n", encoding="utf-8")
            stdout, stderr = waiter.communicate(timeout=2)
            holder.wait(timeout=2)
            self.assertTrue(blocked, "waiter should still be blocked by the live queue lock")
            self.assertEqual(waiter.returncode, 0, stderr or stdout)
            recovery = json.loads((wd / "internal" / "recovery.json").read_text(encoding="utf-8"))
            self.assertEqual(recovery["operational_queue"]["nonterminal_count"], 1)

    def test_queue_lock_reclaims_old_orphan_without_owner_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "20260711-191000_orphan-lock"
            run("init", str(wd), "--objective", "orphan lock recovery")
            lock_path = wd / "internal" / "locks" / "tasks.lock"
            lock_path.mkdir()
            old = time.time() - 10
            os.utime(lock_path, (old, old))
            probe_code = (
                "from pathlib import Path; from lll_cli.main import queue_lock; "
                f"wd=Path({str(wd)!r}); "
                "lock=queue_lock(wd, 'reclaimer', ttl_seconds=1, wait_seconds=0.1); "
                "lock.__enter__(); print('acquired'); lock.__exit__(None, None, None)"
            )
            probe = subprocess.run(
                [sys.executable, "-c", probe_code], cwd=str(ROOT), env=ENV, text=True, capture_output=True,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertIn("acquired", probe.stdout)
            self.assertFalse(lock_path.exists())

    def test_queue_lock_uses_directory_ttl_for_malformed_owner_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "20260711-192000_malformed-lock"
            run("init", str(wd), "--objective", "malformed owner fallback")
            lock_path = wd / "internal" / "locks" / "tasks.lock"
            lock_path.mkdir()
            (lock_path / "owner.json").write_text("{broken", encoding="utf-8")
            probe_code = (
                "from pathlib import Path; from lll_cli.main import queue_lock; "
                f"wd=Path({str(wd)!r}); "
                "lock=queue_lock(wd, 'waiter', ttl_seconds=10, wait_seconds=0.1); "
                "lock.__enter__(); print('acquired'); lock.__exit__(None, None, None)"
            )
            fresh = subprocess.run(
                [sys.executable, "-c", probe_code], cwd=str(ROOT), env=ENV, text=True, capture_output=True,
            )
            self.assertNotEqual(fresh.returncode, 0)
            self.assertIn("queue locked after waiting 0.1s", fresh.stderr)
            self.assertTrue(lock_path.exists())

            old = time.time() - 20
            os.utime(lock_path, (old, old))
            stale = subprocess.run(
                [sys.executable, "-c", probe_code], cwd=str(ROOT), env=ENV, text=True, capture_output=True,
            )
            self.assertEqual(stale.returncode, 0, stale.stderr)
            self.assertIn("acquired", stale.stdout)
            self.assertFalse(lock_path.exists())

            lock_path.mkdir()
            (lock_path / "owner.json").write_text('{"ttl_seconds":0}', encoding="utf-8")
            incomplete = subprocess.run(
                [sys.executable, "-c", probe_code], cwd=str(ROOT), env=ENV, text=True, capture_output=True,
            )
            self.assertNotEqual(incomplete.returncode, 0)
            self.assertIn("queue locked after waiting 0.1s", incomplete.stderr)
            self.assertTrue(lock_path.exists())

    def test_queue_lock_cleans_up_when_owner_metadata_publish_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "20260711-193000_owner-publish-failure"
            run("init", str(wd), "--objective", "owner metadata cleanup")
            probe_code = (
                "from pathlib import Path; import lll_cli.main as m; "
                f"wd=Path({str(wd)!r}); original=m.atomic_write; "
                "m.atomic_write=lambda path,text: (_ for _ in ()).throw(OSError('publish failed')) if path.name=='owner.json' else original(path,text); "
                "lock=m.queue_lock(wd, 'publisher'); "
                "\ntry: lock.__enter__()\nexcept OSError: print('failed-cleanly')\n"
            )
            probe = subprocess.run(
                [sys.executable, "-c", probe_code], cwd=str(ROOT), env=ENV, text=True, capture_output=True,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertIn("failed-cleanly", probe.stdout)
            self.assertFalse((wd / "internal" / "locks" / "tasks.lock").exists())

    def test_task_metadata_carrier_preset_executor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "20260620-162323_cli-metadata"
            run("init", str(wd), "--objective", "metadata")
            report = json.loads(run("task", "add", str(wd), "--title", "research", "--goal", "inspect", "--carrier", "agent_cli", "--preset", "deep-research", "--executor", "shell", "--command", "true", "--json").stdout)
            task = report["task"]
            self.assertEqual(task["carrier"], "agent_cli")
            self.assertEqual(task["preset"], "deep-research")
            self.assertEqual(task["executor"], "shell")
            task_file = (wd / "internal" / "agents" / "T001" / "task.md").read_text(encoding="utf-8")
            self.assertIn("carrier: agent_cli", task_file)
            events = [(json.loads(line)) for line in (wd / "internal" / "runs.jsonl").read_text(encoding="utf-8").splitlines() if line]
            queued = [e for e in events if e.get("event") == "queued"][-1]
            self.assertEqual(queued["carrier"], "agent_cli")
            listed = json.loads(run("task", "list", str(wd), "--json").stdout)
            self.assertEqual(listed["schema"], "lll.task.list.v1")
            self.assertEqual(listed["tasks"][0]["carrier"], "agent_cli")
            nested_out = run("task", "add", str(wd), "--id", "T002", "--title", "bad out", "--goal", "reject nested worker root", "--out", "internal/agents/T002/artifacts/", "--json", check=False)
            self.assertNotEqual(nested_out.returncode, 0)
            self.assertIn("must be exactly internal/agents/<task-id>/", nested_out.stderr)

    def test_workdir_name_validation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "20260620-no-time"
            run("init", str(bad), "--objective", "bad name")
            report = json.loads(run("validate", str(bad), "--json").stdout)
            self.assertTrue(report["ok"])
            self.assertFalse(report["name"]["ok"])
            strict = run("validate", str(bad), "--json", "--strict-name", check=False)
            strict_report = json.loads(strict.stdout)
            self.assertNotEqual(strict.returncode, 0)
            self.assertFalse(strict_report["ok"])
            self.assertIn("non-recommended workdir name", "\n".join(strict_report["messages"]))
            root = Path(td)
            listing = json.loads(run("list", "--root", str(root), "--all", "--json").stdout)
            self.assertEqual(listing["schema"], "lll.list.v1")
            self.assertFalse(listing["workdirs"][0]["name_validation"]["ok"])

    def test_legacy_root_queue_with_mission_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "legacy"
            wd.mkdir()
            (wd / "mission.md").write_text("# Legacy mission\n", encoding="utf-8")
            task = {"id": "legacy-1", "title": "legacy task", "status": "pending", "priority": 1}
            (wd / "tasks.jsonl").write_text(json.dumps(task) + "\n", encoding="utf-8")
            report = json.loads(run("status", str(wd), "--json").stdout)
            self.assertEqual(report["layout"], "legacy_or_transitional")
            self.assertEqual(report["counts"]["pending"], 1)
            self.assertEqual(report["tasks"][0]["id"], "legacy-1")

    def test_failed_task_and_reaper(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "work"
            run("init", str(wd), "--objective", "fail")
            run("task", "add", str(wd), "--title", "bad", "--goal", "fail", "--command", "exit 7", "--max-attempts", "1")
            cp = run("run", "once", str(wd), "--json", check=False)
            self.assertNotEqual(cp.returncode, 0)
            fail_report = json.loads(cp.stdout)
            self.assertEqual(fail_report["schema"], "lll.run.once.v1")
            self.assertFalse(fail_report["ok"])
            self.assertEqual(fail_report["status"], "failed_terminal")
            data = json.loads(run("status", str(wd), "--json").stdout)
            self.assertEqual(data["counts"].get("failed_terminal"), 1)
            reaper_report = json.loads(run("run", "reaper", str(wd), "--json").stdout)
            self.assertEqual(reaper_report["schema"], "lll.run.reaper.v1")

    def test_service_render(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "work"
            run("init", str(wd), "--objective", "svc")
            systemd_report = json.loads(run("service", "install", str(wd), "--target", "systemd", "--user", "--json").stdout)
            self.assertEqual(systemd_report["schema"], "lll.service.install.v1")
            run("service", "install", str(wd), "--target", "launchd")
            run("service", "install", str(wd), "--target", "windows-task")
            service_dir = wd / "internal" / "service"
            self.assertTrue(any(service_dir.glob("*.service")))
            self.assertTrue(any(service_dir.glob("*.plist")))
            self.assertTrue(any(service_dir.glob("*.ps1")))

    def test_audit_append_and_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "20260702-120000_audit-closeout"
            run("init", str(wd), "--objective", "audit")
            audit = json.loads(run("audit", "append", str(wd), "--stream", "trace", "--field", "type=correction", "--field", "item=demo", "--field", "status=superseded", "--message", "corrected", "--json").stdout)
            self.assertEqual(audit["schema"], "lll.audit.append.v1")
            rows = [json.loads(line) for line in (wd / "internal" / "traceability.jsonl").read_text(encoding="utf-8").splitlines() if line]
            self.assertEqual(rows[-1]["type"], "correction")
            validation = json.loads(run("validation", "set", str(wd), "--verdict", "PASS_WITH_NOTES", "--scope", "smoke", "--summary", "checked", "--validator", "unittest", "--evidence", "internal/traceability.jsonl", "--json").stdout)
            self.assertEqual(validation["schema"], "lll.validation.set.v1")
            self.assertEqual(validation["validation"]["verdict"], "PASS_WITH_NOTES")
            shown = json.loads(run("validation", "show", str(wd), "--json").stdout)
            self.assertEqual(shown["validation"]["validator"], "unittest")
            closeout = json.loads(run("closeout", str(wd), "--json", "--write-report").stdout)
            self.assertEqual(closeout["schema"], "lll.closeout.v1")
            self.assertTrue(closeout["ok"])
            self.assertTrue((wd / "internal" / "closeout-report.json").exists())


if __name__ == "__main__":
    unittest.main()
