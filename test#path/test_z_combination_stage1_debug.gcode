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
G28
G29
G21
G91
M204 S3000
G90

G0 X10 Y0 Z5
M204 S9000
G1 X20 Y0 Z0.3 F3000
M204 S3000
G1 X20 Y10 Z0.3 F3000
G1 X10 Y10 Z0.3 F3000
M204 S9000
G1 X10 Y0 Z0.3 F3000

G28
M107
