from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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

    def test_init_task_validate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "work"
            init_report = json.loads(run("init", str(wd), "--objective", "smoke", "--json").stdout)
            self.assertEqual(init_report["schema"], "lll.init.v1")
            self.assertTrue(init_report["ok"])
            add_report = json.loads(run("task", "add", str(wd), "--title", "demo", "--goal", "write marker", "--command", "printf ok > marker.txt", "--verify", "test -f marker.txt", "--max-attempts", "1", "--json").stdout)
            self.assertEqual(add_report["schema"], "lll.task.add.v1")
            self.assertEqual(add_report["task"]["id"], "T001")
            cp = run("status", str(wd), "--json")
            data = json.loads(cp.stdout)
            self.assertEqual(data["schema"], "lll.status.v1")
            self.assertEqual(data["counts"].get("pending"), 1)
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
            checkpoint_report = json.loads(run("checkpoint", str(wd), "--checkpoint", "smoke", "--json").stdout)
            self.assertEqual(checkpoint_report["schema"], "lll.checkpoint.v1")

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


if __name__ == "__main__":
    unittest.main()
