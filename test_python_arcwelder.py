#!/usr/bin/env python3
"""Guarded Python subprocess ArcWelder test.

This test intentionally targets a Windows-only local setup.
"""

import os
import subprocess

import pytest


pytestmark = pytest.mark.skipif(
    os.name != "nt",
    reason="Requires Windows path and ArcWelder local installation",
)


def test_python_subprocess_arcwelder_command():
    os.chdir(r"c:\ArcWelder\Skript")

    cmd = [
        ".\\ArcWelder.exe",
        "test_simple.gcode",
        "test_output_py.gcode",
        "-t=0.10",
        "-r=0.05",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr or result.stdout
    assert os.path.exists("test_output_py.gcode"), "ArcWelder did not create output file"
    assert os.path.getsize("test_output_py.gcode") > 0, "Output file is empty"
