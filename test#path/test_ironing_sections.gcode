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
; Test ironing detection
G28
G92 X0 Y0 Z0.2
M204 S6000
; Regular perimeter moves
G1 X10 Y0 F3000 E1.5
M204 S9000
G1 Z0.2000 F3000
M204 S6000
G1 X10 Y10 F3000 E3.0
M204 S9000
G1 Z0.4000 F3000
M204 S6000
G1 X0 Y10 F3000 E4.5
M204 S9000
G1 Z0.6000 F3000
M204 S6000
G1 X0 Y0 F3000 E6.0
;TYPE:Ironing
; Now we're in ironing section - ZAA should NOT apply here
G1 X10 Y0 F1000 E6.5
G1 X10 Y10 F1000 E7.0
G1 X0 Y10 F1000 E7.5
G1 X0 Y0 F1000 E8.0
;TYPE:Perimeter
; Back to perimeter - ZAA should apply again
M204 S9000
G1 Z0.8000 F3000
M204 S6000
G1 X10 Y0 F3000 E8.5
M204 S9000
G1 Z1.0000 F3000
M204 S6000
G1 X10 Y10 F3000 E9.0
M104 S0
