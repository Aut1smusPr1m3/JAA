; Postprocessed by [ArcWelder](https://github.com/FormerLurker/ArcWelderLib)
; Copyright(C) 2021 - Brad Hochgesang
; Version: 1.2.0, Branch: HEAD, BuildDate: 2021-11-21T20:25:43Z
; resolution=0.06mm
; path_tolerance=12.0%
; max_radius=9999.00mm
; allow_3d_arcs=True
; allow_dynamic_precision=True
; default_xyz_precision=3
; default_e_precision=5
; extrusion_rate_variance_percent=5.0%

; GCodeZAA Enhanced - Tensor Batching, Physics Compensation, Vector Retraction, Non-planar Ironing
; Postprocessed by [ArcWelder](https://github.com/FormerLurker/ArcWelderLib)
; Copyright(C) 2021 - Brad Hochgesang
; Version: 1.2.0, Branch: HEAD, BuildDate: 2021-11-21T20:25:43Z
; resolution=0.06mm
; path_tolerance=12.0%
; max_radius=9999.00mm
; allow_3d_arcs=True
; allow_dynamic_precision=True
; default_xyz_precision=3
; default_e_precision=5
; extrusion_rate_variance_percent=5.0%

; GCodeZAA Enhanced - Tensor Batching, Physics Compensation, Vector Retraction, Non-planar Ironing
; Postprocessed by [ArcWelder](https://github.com/FormerLurker/ArcWelderLib)
; Copyright(C) 2021 - Brad Hochgesang
; Version: 1.2.0, Branch: HEAD, BuildDate: 2021-11-21T20:25:43Z
; resolution=0.06mm
; path_tolerance=12.0%
; max_radius=9999.00mm
; allow_3d_arcs=True
; allow_dynamic_precision=True
; default_xyz_precision=3
; default_e_precision=5
; extrusion_rate_variance_percent=5.0%

; GCodeZAA Enhanced - Tensor Batching, Physics Compensation, Vector Retraction, Non-planar Ironing
; Postprocessed by [ArcWelder](https://github.com/FormerLurker/ArcWelderLib)
; Copyright(C) 2021 - Brad Hochgesang
; Version: 1.2.0, Branch: HEAD, BuildDate: 2021-11-21T20:25:43Z
; resolution=0.06mm
; path_tolerance=12.0%
; max_radius=9999.00mm
; allow_3d_arcs=True
; allow_dynamic_precision=True
; default_xyz_precision=3
; default_e_precision=5
; extrusion_rate_variance_percent=5.0%

; GCodeZAA Enhanced - Tensor Batching, Physics Compensation, Vector Retraction, Non-planar Ironing
; Comprehensive test demonstrating fixed Z combination
G28
G29
G90

G1 F3000
; Test section 1: Basic perimeter with edges
M204 S9000

; Test section 2: Variable feedrate

; Test section 3: Rapid moves (should not get ZAA)
G0 X0 Y0 Z2

M104 S0
