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
; Large test with many corners - shows batch processing
G28
G92 X0 Y0 Z0.2
M104 S210
G1 F3000
; Generate pattern with many corners
G1 X5 Y0
M204 S16100
M204 S9000
G1 Z0.2000 F3000
M204 S16100
G1 X5 Y5
M204 S9000
G1 Z0.4000 F3000
M204 S16100
G1 X10 Y5
M204 S9000
G1 Z0.6000 F3000
M204 S16100
G1 X10 Y0
M204 S9000
G1 Z0.8000 F3000
M204 S16100
G1 X15 Y0
M204 S9000
G1 Z1.0000 F3000
M204 S16100
G1 X15 Y5
M204 S9000
G1 Z1.2000 F3000
M204 S16100
G1 X20 Y5
M204 S9000
G1 Z1.4000 F3000
M204 S16100
G1 X20 Y0
M204 S9000
G1 Z1.6000 F3000
M204 S16100
G1 X25 Y0
M204 S9000
G1 Z1.8000 F3000
M204 S16100
G1 X25 Y5
M204 S9000
G1 Z2.0000 F3000
M204 S16100
G1 X30 Y5
M204 S9000
G1 Z2.2000 F3000
M204 S16100
G1 X30 Y0
; Ironing section
;TYPE:Ironing
M204 S9000
G1 Z2.5000 F3000
M204 S16100
G1 X35 Y0 F1000
M204 S9000
G1 Z2.8000 F3000
M204 S16100
G1 X35 Y5 F1000
M204 S9000
G1 Z3.1000 F3000
M204 S16100
G1 X40 Y5 F1000
M204 S9000
G1 Z3.4000 F3000
M204 S16100
G1 X40 Y0 F1000
;TYPE:Perimeter
; Resume normal moves
M204 S9000
G1 Z2.4000 F3000
M204 S16100
G1 X45 Y0 F3000
M204 S9000
G1 Z2.6000 F3000
M204 S16100
G1 X45 Y5 F3000
M204 S9000
G1 Z2.8000 F3000
M204 S16100
G1 X50 Y5 F3000
M204 S9000
G1 Z3.0000 F3000
M204 S16100
G1 X50 Y0 F3000
M204 S9000
G1 Z3.2000 F3000
M204 S16100
G1 X55 Y0 F3000
M204 S9000
G1 Z3.4000 F3000
M204 S16100
G1 X55 Y5 F3000
M204 S9000
G1 Z3.6000 F3000
M204 S16100
G1 X60 Y5 F3000
M204 S9000
G1 Z3.8000 F3000
M204 S16100
G1 X60 Y0 F3000
M204 S9000
G1 Z4.0000 F3000
M204 S16100
G1 X65 Y0 F3000
M204 S9000
G1 Z4.2000 F3000
M204 S16100
G1 X65 Y5 F3000
M104 S0
G28
