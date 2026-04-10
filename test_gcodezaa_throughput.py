#!/usr/bin/env python3
"""Throughput guard tests for GCodeZAA raycasting pipeline."""

import sys

sys.path.insert(0, "GCodeZAA")

from gcodezaa.context import ProcessorContext
from gcodezaa.process import (
    _is_extruding_move,
    _should_apply_surface_following,
    process_line,
)
from gcodezaa import surface_analysis
from gcodezaa.surface_analysis import MAX_SEGMENT_SAMPLES, SurfaceAnalyzer


class _CountingAnalyzer:
    def __init__(self):
        self.scene = object()
        self.calls = 0

    def analyze_segment_batch(self, *args, **kwargs):
        self.calls += 1
        return []

    def batch_analyze_points(self, *args, **kwargs):
        self.calls += 1
        return []


def _context_for_line(line: str) -> ProcessorContext:
    ctx = ProcessorContext([line], ".")
    ctx.gcode_line = 0
    ctx.active_object = object()
    ctx.line_type = "outer wall"
    ctx.relative_positioning = False
    ctx.wipe = False
    ctx.last_p = (0.0, 0.0, 0.2)
    return ctx


def test_is_extruding_move_absolute_and_relative_modes():
    ctx = _context_for_line("G1 X1 Y1 E1.0\n")
    ctx.relative_extrusion = False
    ctx.last_e = 1.0

    assert _is_extruding_move(ctx, 1.01) is True
    assert _is_extruding_move(ctx, 1.0) is False
    assert _is_extruding_move(ctx, None) is False

    ctx.relative_extrusion = True
    assert _is_extruding_move(ctx, 0.01) is True
    assert _is_extruding_move(ctx, 0.0) is False
    assert _is_extruding_move(ctx, -0.05) is False


def test_should_apply_surface_following_requires_qualifying_move():
    ctx = _context_for_line("G1 X1 Y1 E1.0\n")
    ctx.relative_extrusion = False
    ctx.last_e = 0.5

    assert _should_apply_surface_following(ctx, 1.0) is True

    ctx.wipe = True
    assert _should_apply_surface_following(ctx, 1.0) is False
    ctx.wipe = False

    ctx.line_type = "infill"
    assert _should_apply_surface_following(ctx, 1.0) is False


def test_process_line_skips_raycast_for_non_extrusion_moves():
    analyzer = _CountingAnalyzer()

    travel_ctx = _context_for_line("G1 X10 Y0 F1800\n")
    travel_ctx.relative_extrusion = False
    travel_ctx.last_e = 3.0
    process_line(travel_ctx, analyzer)

    same_e_ctx = _context_for_line("G1 X20 Y0 E3.0 F1800\n")
    same_e_ctx.relative_extrusion = False
    same_e_ctx.last_e = 3.0
    process_line(same_e_ctx, analyzer)

    assert analyzer.calls == 0


def test_analyze_segment_batch_caps_samples_for_long_segments():
    analyzer = SurfaceAnalyzer(None)

    analysis = analyzer.analyze_segment_batch(
        x1=0.0,
        y1=0.0,
        z=0.2,
        x2=200.0,
        y2=0.0,
        layer_height=0.2,
        sample_distance=0.01,
    )

    assert 2 <= len(analysis) <= MAX_SEGMENT_SAMPLES


def test_analyze_segment_batch_skips_implausible_segments():
    analyzer = SurfaceAnalyzer(None)

    analysis = analyzer.analyze_segment_batch(
        x1=0.0,
        y1=0.0,
        z=0.2,
        x2=5000.0,
        y2=0.0,
        layer_height=0.2,
        sample_distance=0.2,
    )

    assert analysis == []


def test_surface_follow_segment_limit_sanitization_bounds():
    assert surface_analysis._sanitize_surface_follow_segment_limit(1.0) == 10.0
    assert surface_analysis._sanitize_surface_follow_segment_limit(1000.0) == 1000.0
    assert surface_analysis._sanitize_surface_follow_segment_limit(999999.0) == 5000.0
