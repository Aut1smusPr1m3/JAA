; GCodeZAA Enhanced - Tensor Batching, Physics Compensation, Vector Retraction, Non-planar Ironing
G28
G29
G90
G1 F3000

; Test perimeter with edges
G1 X10 Y0
G1 X10 Y10
G1 X20 Y10
G1 X20 Y0

; Variable feedrate
G1 X30 Y0 F1500
G1 X30 Y10
G1 X40 Y10
G1 X40 Y0 F3000

G28
M104 S0
