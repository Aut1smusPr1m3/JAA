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
G1 F3000
; Sharp corners that trigger edges
G1 X10 Y0
G1 X10 Y10 Z0.3000
G1 X20 Y10 Z0.6000
G1 X20 Y0 Z0.9000
;TYPE:Ironing
; This is ironing - edges here should get surface-following ZAA
G1 X30 Y0 F1000 Z1.2000
G1 X30 Y10 F1000 Z1.5000

G28
