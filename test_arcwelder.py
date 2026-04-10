#!/usr/bin/env python3
"""Guarded ArcWelder smoke tests.

These tests are Windows-specific because they rely on legacy local paths.
"""

import os
import subprocess
import tempfile

import pytest


SCRIPT_DIR = r"c:\ArcWelder\Skript"
ARCWELDER_EXE = os.path.join(SCRIPT_DIR, "ArcWelder.exe")


pytestmark = pytest.mark.skipif(
    os.name != "nt",
    reason="ArcWelder smoke tests require Windows local ArcWelder installation",
)


def _find_test_gcode() -> str:
    for name in os.listdir(SCRIPT_DIR):
        if name.endswith(".gcode"):
            return os.path.join(SCRIPT_DIR, name)
    pytest.skip("No .gcode file found in ArcWelder script directory")


def test_arcwelder_executable_exists():
    assert os.path.isfile(ARCWELDER_EXE), "ArcWelder.exe was not found in expected directory"


def test_arcwelder_basic_command():
    if not os.path.isfile(ARCWELDER_EXE):
        pytest.skip("ArcWelder executable missing")

    test_gcode = _find_test_gcode()
    fd, temp_output = tempfile.mkstemp(suffix=".gcode", text=True)
    os.close(fd)

    try:
        cmd = [ARCWELDER_EXE, "-t=0.10", "-r=0.05", test_gcode, temp_output]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr or result.stdout
        assert os.path.exists(temp_output), "ArcWelder did not create output file"
        assert os.path.getsize(temp_output) > 0, "ArcWelder output file is empty"
    finally:
        if os.path.exists(temp_output):
            os.remove(temp_output)
