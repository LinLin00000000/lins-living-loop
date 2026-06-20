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

    def test_init_task_validate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "work"
            run("init", str(wd), "--objective", "smoke")
            run("task", "add", str(wd), "--title", "demo", "--goal", "write marker", "--command", "printf ok > marker.txt", "--verify", "test -f marker.txt", "--max-attempts", "1")
            cp = run("status", str(wd), "--json")
            data = json.loads(cp.stdout)
            self.assertEqual(data["counts"].get("pending"), 1)
            run("validate", str(wd))
            rc = run("run", "once", str(wd))
            self.assertEqual(rc.returncode, 0)
            data = json.loads(run("status", str(wd), "--json").stdout)
            self.assertEqual(data["counts"].get("succeeded"), 1)
            artifacts = list((wd / "internal" / "agents" / "T001" / "artifacts").glob("runner-run-*/result.json"))
            self.assertTrue(artifacts)

    def test_failed_task_and_reaper(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "work"
            run("init", str(wd), "--objective", "fail")
            run("task", "add", str(wd), "--title", "bad", "--goal", "fail", "--command", "exit 7", "--max-attempts", "1")
            cp = run("run", "once", str(wd), check=False)
            self.assertNotEqual(cp.returncode, 0)
            data = json.loads(run("status", str(wd), "--json").stdout)
            self.assertEqual(data["counts"].get("failed_terminal"), 1)
            run("run", "reaper", str(wd))

    def test_service_render(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wd = Path(td) / "work"
            run("init", str(wd), "--objective", "svc")
            run("service", "install", str(wd), "--target", "systemd", "--user")
            run("service", "install", str(wd), "--target", "launchd")
            run("service", "install", str(wd), "--target", "windows-task")
            service_dir = wd / "internal" / "service"
            self.assertTrue(any(service_dir.glob("*.service")))
            self.assertTrue(any(service_dir.glob("*.plist")))
            self.assertTrue(any(service_dir.glob("*.ps1")))


if __name__ == "__main__":
    unittest.main()
