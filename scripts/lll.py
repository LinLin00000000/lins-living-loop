#!/usr/bin/env python3
"""Compatibility shim for the standalone `lll` CLI package."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lll_cli.main import main  # noqa: E402

raise SystemExit(main())
