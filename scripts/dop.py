#!/usr/bin/env python3
"""Compatibility wrapper for the old DOP helper name.

The public name is now Lin's Living Loop / LLL. Existing docs, scripts, and
old workdirs may still call `dop.py`, so this shim forwards to `lll.py`.
"""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("lll.py")), run_name="__main__")
