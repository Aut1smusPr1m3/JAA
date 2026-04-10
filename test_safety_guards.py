#!/usr/bin/env python3
"""Safety regression tests for build-plate Z guards."""

from pathlib import Path

from GCodeZAA.gcodezaa.process import clamp_buildplate_z
from GCodeZAA.gcodezaa.surface_analysis import MAX_SMOOTHING_ANGLE as SURFACE_MAX_SMOOTHING_ANGLE
from Ultra_Optimizer import (
    MIN_BUILDPLATE_Z,
    ZAA_MAX_SMOOTHING_ANGLE,
    count_negative_z_commands,
    enforce_non_negative_z_in_gcode,
)


def test_clamp_buildplate_z_enforces_floor():
    assert clamp_buildplate_z(None) is None
    assert clamp_buildplate_z(0.15) == 0.15
    assert clamp_buildplate_z(-0.2) == MIN_BUILDPLATE_Z


def test_smoothing_angle_is_hard_capped_for_safety():
    assert ZAA_MAX_SMOOTHING_ANGLE <= 45.0
    assert SURFACE_MAX_SMOOTHING_ANGLE <= 45.0


def test_enforce_non_negative_z_clamps_absolute_moves(tmp_path: Path):
    gcode_file = tmp_path / "absolute_negative.gcode"
    gcode_file.write_text(
        "".join(
            [
                "G90\n",
                "G1 X0 Y0 Z0.20 F1200\n",
                "G1 X1 Y1 Z-0.10 F1200\n",
            ]
        ),
        encoding="utf-8",
    )

    assert count_negative_z_commands(str(gcode_file)) == 1
    clamped = enforce_non_negative_z_in_gcode(str(gcode_file))
    assert clamped == 1
    assert count_negative_z_commands(str(gcode_file)) == 0

    output = gcode_file.read_text(encoding="utf-8")
    assert "Z-0.10" not in output


def test_enforce_non_negative_z_clamps_relative_moves(tmp_path: Path):
    gcode_file = tmp_path / "relative_negative.gcode"
    gcode_file.write_text(
        "".join(
            [
                "G90\n",
                "G1 Z0.05\n",
                "G91\n",
                "G1 Z-0.10 F600\n",
                "G90\n",
            ]
        ),
        encoding="utf-8",
    )

    assert count_negative_z_commands(str(gcode_file)) == 1
    clamped = enforce_non_negative_z_in_gcode(str(gcode_file))
    assert clamped == 1
    assert count_negative_z_commands(str(gcode_file)) == 0

    output = gcode_file.read_text(encoding="utf-8")
    assert "G1 Z-0.05 F600" in output


def test_enforce_non_negative_z_clamps_g92_set_position(tmp_path: Path):
    gcode_file = tmp_path / "g92_negative.gcode"
    gcode_file.write_text(
        "".join(
            [
                "G90\n",
                "G92 Z-1.00\n",
                "G1 X1 Y1 Z0.10\n",
            ]
        ),
        encoding="utf-8",
    )

    assert count_negative_z_commands(str(gcode_file)) == 1
    clamped = enforce_non_negative_z_in_gcode(str(gcode_file))
    assert clamped == 1
    assert count_negative_z_commands(str(gcode_file)) == 0

    output = gcode_file.read_text(encoding="utf-8")
    assert "G92 Z0" in output
