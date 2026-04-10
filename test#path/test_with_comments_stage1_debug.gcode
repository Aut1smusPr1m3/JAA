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
