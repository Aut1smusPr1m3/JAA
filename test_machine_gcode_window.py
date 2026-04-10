#!/usr/bin/env python3
"""Tests for printable window detection and start/end machine G-code passthrough."""

from pathlib import Path
import sys

from Ultra_Optimizer import detect_machine_print_window, process_gcode

sys.path.insert(0, "GCodeZAA")

from gcodezaa.process import detect_processing_window
from gcodezaa.slicer_syntax import SlicerSyntax, Slicer


def test_detect_machine_print_window_prefers_executable_block():
    lines = [
        ";start\n",
        "; printing object foo\n",
        "; EXECUTABLE_BLOCK_START\n",
        "G1 X1 Y1\n",
        "; EXECUTABLE_BLOCK_END\n",
        "; stop printing object foo\n",
    ]

    start, end, reason = detect_machine_print_window(lines)
    assert (start, end, reason) == (2, 4, "executable-block")


def test_detect_machine_print_window_uses_print_object_markers():
    lines = [
        ";start\n",
        "; printing object foo\n",
        "G1 X1 Y1\n",
        "; stop printing object foo\n",
        ";end\n",
    ]

    start, end, reason = detect_machine_print_window(lines)
    assert (start, end, reason) == (1, 3, "printing-object-comments")


def test_gcodezaa_window_detector_matches_print_object_behavior():
    lines = [
        ";start\n",
        "; printing object foo\n",
        "G1 X1 Y1\n",
        "; stop printing object foo\n",
        ";end\n",
    ]
    syntax = SlicerSyntax(Slicer.ORCA)

    start, end, reason = detect_processing_window(lines, syntax)
    assert (start, end, reason) == (1, 3, "printing-object-comments")


def test_stage1_leaves_machine_start_and_end_unmodified(tmp_path: Path):
    gcode_file = tmp_path / "window_test.gcode"
    original_lines = [
        ";MACHINE_START\n",
        "G1 X0 Y0 Z0.20 F1200\n",
        "; printing object demo\n",
        "G1 X5 Y5 Z0.20 F1200\n",
        "; stop printing object demo\n",
        ";MACHINE_END\n",
        "G1 X0 Y0 Z10.00 F1200\n",
    ]
    gcode_file.write_text("".join(original_lines), encoding="utf-8")

    process_gcode(str(gcode_file))
    output = gcode_file.read_text(encoding="utf-8").splitlines(keepends=True)

    assert output[0] == original_lines[0]
    assert output[1] == original_lines[1]
    assert output[-2] == original_lines[-2]
    assert output[-1] == original_lines[-1]
