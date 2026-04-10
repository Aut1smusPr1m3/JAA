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
; Test file for ZAA heuristic Z compensation
; Should see Z movements injected at corners due to angle changes
G28
G92 X0 Y0 Z0.2
M204 S6000  ; Start with lower accel
G1 X10 Y0 F3000 E1.5
G1 Z0.2000 F3000
G1 X10 Y10 F3000 E3.0
G1 Z0.4000 F3000
G1 X20 Y10 F3000 E4.5
G1 Z0.6000 F3000
G1 X20 Y0 F3000 E6.0
G1 Z0.8000 F3000
G1 X30 Y0 F3000 E7.5
G1 Z1.0000 F3000
G1 X30 Y20 F3000 E9.0
G1 Z1.2000 F3000
G1 X40 Y20 F3000 E10.5
G1 Z1.4000 F3000
G1 X40 Y5 F3000 E12.0
; Now some regular moves
G1 Z1.6000 F3000
G1 X50 Y5 F3000 E13.5
G1 Z1.8000 F3000
G1 X50 Y25 F3000 E15.0
M104 S0
M109 R0
G28
