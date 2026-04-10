#!/usr/bin/env python3
"""Regression tests for relative/absolute extrusion state continuity in GCodeZAA."""

import sys

sys.path.insert(0, "GCodeZAA")

from gcodezaa.process import EdgeDetector, SurfaceAnalyzer, process_line
from gcodezaa.context import ProcessorContext


def _process_all_lines(ctx: ProcessorContext):
    analyzer = SurfaceAnalyzer(None)
    edge_detector = EdgeDetector()
    for idx in range(len(ctx.gcode)):
        ctx.gcode_line = idx
        process_line(ctx, analyzer, edge_detector)


def test_relative_extrusion_running_total_updates_last_e():
    gcode = [
        "M83\n",
        "G1 X1.0 Y0.0 E0.50 F1200\n",
        "G1 X2.0 Y0.0 E0.25\n",
    ]
    ctx = ProcessorContext(gcode, ".")

    _process_all_lines(ctx)

    assert ctx.relative_extrusion is True
    assert abs(ctx.last_e - 0.75) < 1e-9


def test_absolute_extrusion_sets_last_e_to_absolute_value():
    gcode = [
        "M82\n",
        "G1 X1.0 Y0.0 E2.00 F1200\n",
        "G1 X2.0 Y0.0 E3.50\n",
    ]
    ctx = ProcessorContext(gcode, ".")

    _process_all_lines(ctx)

    assert ctx.relative_extrusion is False
    assert abs(ctx.last_e - 3.50) < 1e-9
