import sys, traceback
from gcodezaa.process import process_gcode

gcode=[
    'G28\n',
    'G92 X0 Y0 Z0 E0\n',
    '; EXECUTABLE_BLOCK_START\n',
    ';TYPE:Ironing\n',
    'G1 X5 Y0 Z0.2 E1.0 F1200\n',
    'G1 X10 Y0 Z0.2 E2.0 F1200\n',
    '; EXECUTABLE_BLOCK_END\n',
]

try:
    process_gcode(gcode, 'stl_models', ('3DBenchy.stl', 0.0, 0.0))
except Exception:
    traceback.print_exc()
    sys.exit(1)
