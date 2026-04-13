# OrcaSlicer Integration

## Post-processing script
Configure OrcaSlicer to run:
- `Ultra_Optimizer.py`

OrcaSlicer passes the generated G-code path as argument to the script.

## Required OrcaSlicer settings
- Enable `Verbose G-code` so feature comments (for example `; FEATURE: Ironing` and `; ironing`) are present.
- Disable `Arc fitting` in OrcaSlicer. Arc conversion should be done by Stage 3 (`ArcWelder.exe`) to avoid double-processing.

## Object placement and rotation alignment
- Stage 2 tries to align STL sampling using object transform metadata.
- Center position is resolved from comment hints, `EXCLUDE_OBJECT_DEFINE CENTER=...`, or printable-window motion bounds.
- Rotation defaults to `0deg` unless explicit metadata is present.

If your sliced object is moved or rotated and Stage 2 looks misaligned, add optional hints to the G-code comments:

```gcode
; ZAA_OBJECT_POSITION: 110.25,128.50
; ZAA_OBJECT_ROTATION_DEG: 37.5
```

Alternative metadata path (commonly emitted by exclusion-capable slicer flows):

```gcode
EXCLUDE_OBJECT_DEFINE NAME=part.stl_0 CENTER=110.25,128.50 ROTATION=37.5
```

## Python interpreter warning
- OrcaSlicer must execute the script with the same project virtual environment used during setup.
- If needed, point OrcaSlicer to the venv interpreter explicitly (for example `.venv/bin/python`).

## Expected behavior
- Script validates input G-code.
- Stage 1 kinematic optimization always runs.
- Stage 2 uses GCodeZAA when available and when an STL is present in `stl_models/`, and logs transform source/values used for model placement.
- Stage 3 ArcWelder runs only if `ArcWelder.exe` exists in repo root.

## Artifacts
- Runtime log: `kinematic_engine.log`
- Output: optimized in-place G-code
