#!/usr/bin/env python
import sys
import os

# Add GCodeZAA to path the same way Ultra_Optimizer does
gcodezaa_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GCodeZAA")
sys.path.insert(0, gcodezaa_path)

try:
    from gcodezaa.process import process_gcode
    print("✓ GCodeZAA import successful - Stage 2 ready!")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
