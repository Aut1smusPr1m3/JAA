# Pre-Flight Checklist - Ultra_Optimizer 2.0

## ✅ Installation Verification

### Files Required
- [ ] `Ultra_Optimizer.py` exists in `C:\ArcWelder\Skript\`
- [ ] `zaa_enhanced.py` exists in `C:\ArcWelder\Skript\`
- [ ] `ArcWelder.exe` exists in `C:\ArcWelder\Skript\`
- [ ] `requirements.txt` current

### Software Requirements
- [ ] Python 3.7+ accessible
- [ ] NumPy installed (`pip list | findstr numpy`)
- [ ] JSON module available (built-in)
- [ ] Subprocess module available (built-in)

### Directory Permissions
- [ ] Can write to `C:\ArcWelder\Skript\` (for logs)
- [ ] Can read G-code input files
- [ ] Can write output G-code files

---

## 🔧 OrcaSlicer Configuration

### Post-Processing Setup
- [ ] OrcaSlicer installed and working
- [ ] Preferences → Post-processing scripts found
- [ ] Full path to Ultra_Optimizer.py copied
  ```
  C:\ArcWelder\Skript\Ultra_Optimizer.py
  ```
- [ ] Path verified (no typos)
- [ ] Settings saved

### Printer Profile
- [ ] Printer profile selected
- [ ] Machine g-code section contains post-processor
- [ ] No conflicting post-processors enabled
- [ ] File format is standard G-code (not UltiGCode)

---

## 📊 Test 1: Simple G1 Moves

**File: `test_simple.gcode`**
```gcode
G28
G1 X10 Y10 F1000
G1 X20 Y20 F1000
G1 X30 Y30 F1000
M104 S0
M109 R0
```

**Expected Results:**
- [ ] Script runs without errors
- [ ] Log file created: `kinematic_engine.log`
- [ ] Output file created: `test_simple_optimized.gcode`
- [ ] Output contains M204 commands
- [ ] G1 commands preserved
- [ ] Validation line shows: `G0=1, G1=3, G2=0, G3=0`

**Check Log:**
```bash
grep "SYSTEM" kinematic_engine.log
```
Should show:
```
[SYSTEM] OrcaSlicer Post-Processing Mode
[SYSTEM] Processing: test_simple.gcode
[VALIDATION] G0=1, G1=3, G2=0, G3=0
[PIPELINE] Stage 1: Kinematic Optimization
[PIPELINE] All-In-One Post-Processing Complete
```

---

## 📊 Test 2: Arc Commands (G2/G3)

**File: `test_arcs.gcode`**
```gcode
G28
G1 X0 Y0 F1000
G2 X10 Y10 I5 J0 F1000
G3 X20 Y0 I5 J0 F1000
M104 S0
```

**Expected Results:**
- [ ] Script runs without errors
- [ ] Log shows arc processing
- [ ] Output contains G2/G3 commands
- [ ] M204 injection before arcs (accel=6000)
- [ ] M204 restoration after arcs (accel=24000)
- [ ] Validation line shows: `G0=1, G1=1, G2=1, G3=1`

**Check Log:**
```bash
grep "Arc (G" kinematic_engine.log
```
Should show:
```
Arc (G2) at line XXX: length=YY.XXmm, accel=6000
Arc (G3) at line XXX: length=YY.XXmm, accel=6000
```

---

## 📊 Test 3: Mixed Commands

**File: `test_mixed.gcode`**
```gcode
G28
G0 X10 Y10 Z0.2
G1 X20 Y20 F1000
M204 S12000
G1 X30 Y30 F1000
G2 X40 Y40 I5 J0 F1000
G3 X50 Y50 I5 J0 F1000
G1 X60 Y60 F1000
```

**Expected Results:**
- [ ] All commands processed
- [ ] G0 resets state
- [ ] G1 lines optimized
- [ ] G2/G3 have reduced acceleration
- [ ] Existing M204 replaced with optimal
- [ ] All commands preserved
- [ ] Validation: `G0=1, G1=3, G2=1, G3=1, M204=X`

**Check Log:**
```bash
grep "VALIDATION" kinematic_engine.log
```

---

## 📊 Test 4: Stage 2 - ArcWelder

**Prerequisites:**
- [ ] ArcWelder.exe in `C:\ArcWelder\Skript\`
- [ ] ArcWelder can execute

**Run Test:**
```bash
# Manual test
python Ultra_Optimizer.py test_mixed.gcode
```

**Expected Results:**
- [ ] Log shows Stage 2 executing
- [ ] ArcWelder compression occurs
- [ ] Output file is reasonable size
- [ ] No ArcWelder errors in log

**Check Log:**
```bash
grep "Stage 2\|ArcWelder" kinematic_engine.log
```
Should show:
```
[PIPELINE] Stage 2: ArcWelder Pipeline
[PIPELINE] ArcWelder integration successful
```

---

## 📊 Test 5: Stage 3 - GCodeZAA (Optional)

**If STL models exist:**

**Prerequisites:**
- [ ] Folder `C:\ArcWelder\Skript\stl_models\` exists
- [ ] STL file named exactly as model
- [ ] Open3D installed: `pip install open3d`

**Run Test:**
```bash
python Ultra_Optimizer.py test_simple.gcode
```

**Expected Results:**
- [ ] Log detects STL files
- [ ] Stage 3 executes
- [ ] Surface analysis complete
- [ ] Output includes sub-layer commands

**Check Log:**
```bash
grep "Stage 3\|GCodeZAA\|STL" kinematic_engine.log
```

---

## 🔍 Log Verification

### Location
- [ ] Log file exists: `C:\ArcWelder\Skript\kinematic_engine.log`
- [ ] File is readable
- [ ] File contains timestamps
- [ ] File contains [SYSTEM] markers

### Key Log Sections to Find

**Startup:**
```
[SYSTEM] OrcaSlicer Post-Processing Mode
[SYSTEM] Processing: <filename>
```

**Stage 1:**
```
[PIPELINE] Stage 1: Kinematic Optimization + ZAA Framework
[VALIDATION] G0=X, G1=Y, G2=Z, G3=W, M204=V
```

**Stage 2:**
```
[PIPELINE] Stage 2: ArcWelder Pipeline
[PIPELINE] ArcWelder integration successful
```

**Stage 3 (if applicable):**
```
[PIPELINE] Stage 3: GCodeZAA Raycasting
Found STL models: [list]
```

**Completion:**
```
[PIPELINE] All-In-One Post-Processing Complete ✓
```

---

## 🎯 OrcaSlicer Integration Test

### Actual Print Test

**Step 1: Simple Model**
- [ ] Open simple geometric model (cube, cylinder)
- [ ] Slice normally
- [ ] Export G-code
- [ ] Verify output file exists

**Step 2: Check Processing**
- [ ] Open `kinematic_engine.log`
- [ ] Search for [SYSTEM] entries
- [ ] Verify Stage 1 completed
- [ ] Verify Stage 2 (if ArcWelder enabled)

**Step 3: Print**
- [ ] Transfer to printer
- [ ] Observe print quality
- [ ] Check for improvements:
  - Smoother acceleration
  - Better surface quality (if STL enabled)
  - Faster completion (if arcs enabled)

---

## 📋 Detailed Log Analysis

### Command Count Check
```bash
# Show validation line
grep "VALIDATION" kinematic_engine.log

# Expected format:
# [VALIDATION] G0=1, G1=150, G2=5, G3=3, M204=8
```

**Verify:** Last validation should match your G-code structure

### Arc Command Check
```bash
# Show all arcs found
grep "Arc (G" kinematic_engine.log

# Expected format:
# Arc (G2) at line XXX: length=YY.XXmm, accel=6000
# Arc (G3) at line XXX: length=YY.XXmm, accel=6000
```

**Verify:** Arc count matches your G-code, accel always 6000

### Performance Check
```bash
# Show processing times
grep "Stage\|Complete" kinematic_engine.log | head -10
```

**Verify:** Processing completes in <2 seconds for typical files

### Error Check
```bash
# Look for errors
grep "ERROR\|FAIL\|except" kinematic_engine.log
```

**Verify:** No errors found, or understand what failed

---

## 🚨 Troubleshooting Checklist

### Script Doesn't Run
- [ ] Python path correct
- [ ] Ultra_Optimizer.py not corrupted
- [ ] Check syntax: `python -m py_compile Ultra_Optimizer.py`
- [ ] Check imports: `python -c "import json, re, logging, subprocess"`

### No Log File Created
- [ ] Directory writable: `echo test > C:\ArcWelder\Skript\test.txt`
- [ ] File permissions correct
- [ ] Ultra_Optimizer.py executed (not just opened)
- [ ] Check output for error messages

### Output File Not Created
- [ ] Input file readable
- [ ] Input file valid G-code
- [ ] Output directory writable
- [ ] Check log for [ERROR] messages

### Arcs Not Optimized
- [ ] ENABLE_ARC_ANALYSIS = True (verify in script)
- [ ] G2/G3 commands in input file
- [ ] Check log for "Arc (G2)" entries
- [ ] Verify accel reduction to 6000

### ArcWelder Not Running
- [ ] ArcWelder.exe exists in same directory
- [ ] Can execute: `ArcWelder.exe` (should show help)
- [ ] Parameters clean (no embedded quotes)
- [ ] Check Stage 2 in log

### GCodeZAA Not Active
- [ ] STL files in `stl_models/` folder
- [ ] STL file names exact match
- [ ] Check for "Found STL models" in log
- [ ] Install Open3D if needed: `pip install open3d`

---

## 📈 Success Indicators

### ✅ Green Light Checklist

- [ ] Script runs silently (no errors)
- [ ] Log file created with [SYSTEM] entries
- [ ] All 3 stages complete (or skip gracefully)
- [ ] Output file generated
- [ ] Output file valid G-code
- [ ] Command counts match input
- [ ] M204 commands injected for moves
- [ ] G2/G3 arcs detected (if present)
- [ ] Arc acceleration = 6000 (if arcs present)
- [ ] No [ERROR] in log
- [ ] [PIPELINE] ...Complete ✓ message present

### 🟡 Yellow Light Checklist (Optional Features)

- [ ] Stage 2 optimal (ArcWelder integration)
- [ ] Stage 3 available (GCodeZAA with STL)
- [ ] Reduced processing time with cache
- [ ] Surface raycasting accuracy

### 🔴 Red Light Checklist (Must Fix)

- [ ] Script errors (Python exception)
- [ ] Log file missing
- [ ] Output file missing or empty
- [ ] Output file invalid G-code
- [ ] Command count mismatch
- [ ] M204 not injected
- [ ] Arc commands lost

---

## 🔄 Quick Validation Run

```bash
# Step 1: Create test file
echo "G28
G1 X10 Y10 F1000
G1 X20 Y20 F1000
G2 X30 Y30 I5 J0 F1000
M104 S0" > test_validation.gcode

# Step 2: Run processor
python Ultra_Optimizer.py test_validation.gcode

# Step 3: Check results
type kinematic_engine.log | find "VALIDATION"
type test_validation_optimized.gcode | find "M204"

# If both commands return output: SUCCESS ✓
```

---

## 🎓 Expected Behavior

### Typical Session Log Flow

```
18:45:23 [SYSTEM] OrcaSlicer Post-Processing Mode
18:45:23 [SYSTEM] Processing: calibration_cube.gcode
18:45:23 [VALIDATION] Input file: 15,842 bytes
18:45:23 [VALIDATION] G0=1, G1=247, G2=0, G3=0, M204=0
18:45:24 [PIPELINE] Stage 1: Kinematic Optimization + ZAA Framework
18:45:24 [PROCESS] G1 optimization at line XXX
18:45:24 [PROCESS] Acceleration profile: 24000 mm/s²
18:45:25 [PIPELINE] Stage 2: ArcWelder Pipeline
18:45:25 [PIPELINE] ArcWelder integration successful
18:45:25 [PIPELINE] Stage 3: GCodeZAA Raycasting (no STL models found)
18:45:25 [VALIDATION] Output file: 16,147 bytes
18:45:25 [VALIDATION] G0=1, G1=247, G2=0, G3=0, M204=8
18:45:25 [PIPELINE] All-In-One Post-Processing Complete ✓
```

**Interpretation:**
- ✅ Script started correctly
- ✅ Input validated
- ✅ Stage 1 processed G1 moves, added 8 M204 commands
- ✅ Stage 2 ran ArcWelder
- ✅ Stage 3 gracefully skipped (no STL files)
- ✅ Output created and verified
- ✅ All components working

---

## 📞 Final Verification

### Before Printing
- [ ] Run through all tests above
- [ ] All logs show "Complete ✓"
- [ ] No errors found
- [ ] Output file valid
- [ ] Ready to print!

### First Print
- [ ] Start simple (calibration cube or benchy)
- [ ] Observe quality improvement
- [ ] Check acceleration smoothness
- [ ] Verify no layer artifacts
- [ ] Monitor log for any issues

### Ongoing
- [ ] Keep `kinematic_engine.log` for debugging
- [ ] Check log for any warnings
- [ ] Rotate STL models regularly (1 per object type)
- [ ] Update parameters if needed for specific models

---

## 🎉 Completion

When all checkboxes above are complete:

✅ **Ultra_Optimizer 2.0 is ready for production use**

Your prints are now optimized with:
- Kinematic acceleration profiling
- Z-Anti-Aliasing framework
- ArcWelder path compression
- G2/G3 arc support
- Optional surface raycasting

**Enjoy smoother, faster, better-quality prints!**
