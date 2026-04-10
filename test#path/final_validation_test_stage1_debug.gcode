; Comprehensive test demonstrating fixed Z combination
G28
G29
G90

G1 F3000
; Test section 1: Basic perimeter with edges
G1 X10 Y0
G1 X10 Y10 Z0.3000
G1 X20 Y10 Z0.6000
G1 X20 Y0 Z0.9000

; Test section 2: Variable feedrate
G1 X30 Y0 F1500 Z1.2000
G1 X30 Y10 Z1.5000

; Test section 3: Rapid moves (should not get ZAA)
G0 X0 Y0 Z2

M104 S0
