#!/usr/bin/env python3
import subprocess
import os

os.chdir("c:\\ArcWelder\\Skript")

# Test with the exact command from our fixed code
cmd = [
    "./ArcWelder.exe",
    "test_simple.gcode",
    "test_output_py.gcode",
    "-d",
    "-y",
    "-z",
    "-t=0.10",
    "-r=0.05",
    "--",
]

# Note: We don't need the -- separator for this simple case
cmd_simple = [
    ".\\ArcWelder.exe",
    "test_simple.gcode",
    "test_output_py.gcode",
    "-t=0.10",
    "-r=0.05",
]

print("Testing Python subprocess call to ArcWelder...")
print(f"Command: {cmd_simple}\n")

result = subprocess.run(cmd_simple, capture_output=True, text=True, timeout=30)

print(f"Return code: {result.returncode}\n")

if result.stdout:
    print("STDOUT:")
    print(result.stdout)

if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

if result.returncode == 0:
    print("\n✓ ArcWelder succeeded!")
    if os.path.exists("test_output_py.gcode"):
        size = os.path.getsize("test_output_py.gcode")
        print(f"Output file size: {size} bytes")
else:
    print(f"\n✗ ArcWelder failed with code {result.returncode}")
