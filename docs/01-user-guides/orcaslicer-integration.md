# OrcaSlicer Integration

## Post-processing script
Configure OrcaSlicer to run:
- `Ultra_Optimizer.py`

OrcaSlicer passes the generated G-code path as argument to the script.

## Required OrcaSlicer settings
- Enable `Verbose G-code` so feature comments (for example `; FEATURE: Ironing` and `; ironing`) are present.
- Disable `Arc fitting` in OrcaSlicer. Arc conversion should be done by Stage 3 (`ArcWelder.exe`) to avoid double-processing.

## Python interpreter warning
- OrcaSlicer must execute the script with the same project virtual environment used during setup.
- If needed, point OrcaSlicer to the venv interpreter explicitly (for example `.venv/bin/python`).

## Expected behavior
- Script validates input G-code.
- Stage 1 kinematic optimization always runs.
- Stage 2 uses GCodeZAA when available and when an STL is present in `stl_models/`.
- Stage 3 ArcWelder runs only if `ArcWelder.exe` exists in repo root.

## Artifacts
- Runtime log: `kinematic_engine.log`
- Output: optimized in-place G-code
