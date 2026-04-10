; Postprocessed by [ArcWelder](https://github.com/FormerLurker/ArcWelderLib)
; Copyright(C) 2021 - Brad Hochgesang
; Version: 1.2.0, Branch: HEAD, BuildDate: 2021-11-21T20:25:43Z
; resolution=0.05mm
; path_tolerance=10.0%
; max_radius=9999.00mm
; default_xyz_precision=3
; default_e_precision=5
; extrusion_rate_variance_percent=5.0%

G28                 ; Home
G29                 ; Auto level
G1 X10 Y10 F1200   ; Move to position
G1 Z0.2 F600       ; Lower nozzle
G1 X20 F1200       ; Draw line
G1 X30 F1200       ; Continue line
G1 X40 F1200       ; Continue line
G1 X50 F1200       ; Continue line
G1 Y20 F1200       ; Move  Y
G1 X40 F1200       ; Move back
G1 X30 F1200       ; Continue
G1 X20 F1200       ; Continue
G1 X10 F1200       ; Return
G1 Z10 F600        ; Raise nozzle
M104 S0             ; Turn off
M109 S0             ; Wait for cool
M84                 ; Disable motors
