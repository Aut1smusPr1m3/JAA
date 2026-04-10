#!/usr/bin/env python3
"""
Test ArcWelder to diagnose the issue
"""
import subprocess
import os
import tempfile
import shutil

script_dir = "c:\\ArcWelder\\Skript"
arcwelder_exe = os.path.join(script_dir, "ArcWelder.exe")

print(f"ArcWelder path: {arcwelder_exe}")
print(f"ArcWelder exists: {os.path.isfile(arcwelder_exe)}")

# Find a test gcode file
test_gcode = None
for f in os.listdir(script_dir):
    if f.endswith('.gcode'):
        test_gcode = os.path.join(script_dir, f)
        break

if not test_gcode:
    print("ERROR: No .gcode file found in script directory!")
    exit(1)

print(f"\nTest G-Code file: {os.path.basename(test_gcode)}")
print(f"File size: {os.path.getsize(test_gcode)} bytes")

# Create temporary output file
fd, temp_output = tempfile.mkstemp(suffix=".gcode", text=True)
os.close(fd)

print(f"\nTemporary output: {temp_output}")

# Test different ArcWelder commands
print("\n" + "="*60)
print("TEST 1: Minimal command (just files)")
print("="*60)
cmd = [arcwelder_exe, test_gcode, temp_output]
print(f"Command: {' '.join(cmd)}\n")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(f"Return code: {result.returncode}")
if result.stdout:
    print(f"STDOUT:\n{result.stdout}")
if result.stderr:
    print(f"STDERR:\n{result.stderr}")
print(f"Output file size: {os.path.getsize(temp_output) if os.path.exists(temp_output) else 'N/A'}")
if os.path.exists(temp_output):
    os.remove(temp_output)

print("\n" + "="*60)
print("TEST 2: With tolerance and resolution")
print("="*60)
cmd = [arcwelder_exe, "-t=0.10", "-r=0.05", test_gcode, temp_output]
print(f"Command: {' '.join(cmd)}\n")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(f"Return code: {result.returncode}")
if result.stdout:
    print(f"STDOUT:\n{result.stdout}")
if result.stderr:
    print(f"STDERR:\n{result.stderr}")
print(f"Output file size: {os.path.getsize(temp_output) if os.path.exists(temp_output) else 'N/A'}")
if os.path.exists(temp_output):
    os.remove(temp_output)

print("\n" + "="*60)
print("TEST 3: With all flags (-d, -y, -z, tolerance, resolution)")
print("="*60)
cmd = [arcwelder_exe, "-d", "-y", "-z", "-t=0.10", "-r=0.05", "--", test_gcode, temp_output]
print(f"Command: {' '.join(cmd)}\n")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(f"Return code: {result.returncode}")
if result.stdout:
    print(f"STDOUT:\n{result.stdout}")
if result.stderr:
    print(f"STDERR:\n{result.stderr}")
print(f"Output file size: {os.path.getsize(temp_output) if os.path.exists(temp_output) else 'N/A'}")
if os.path.exists(temp_output):
    os.remove(temp_output)

print("\n" + "="*60)
print("TEST 4: Check ArcWelder help/version")
print("="*60)
cmd = [arcwelder_exe, "-h"]
print(f"Command: {' '.join(cmd)}\n")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
print(f"Return code: {result.returncode}")
if result.stdout:
    print(f"STDOUT:\n{result.stdout}")
if result.stderr:
    print(f"STDERR:\n{result.stderr}")

# Clean up
if os.path.exists(temp_output):
    os.remove(temp_output)

print("\nDiagnostic test complete!")
