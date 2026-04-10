# OrcaSlicer Integration

## Post-processing script
Configure OrcaSlicer to run:
- `Ultra_Optimizer.py`

OrcaSlicer passes the generated G-code path as argument to the script.

## Expected behavior
- Script validates input G-code.
- Stage 1 kinematic optimization always runs.
- Stage 2 uses GCodeZAA when available and when an STL is present in `stl_models/`.
- Stage 3 ArcWelder runs only if `ArcWelder.exe` exists in repo root.

## Artifacts
- Runtime log: `kinematic_engine.log`
- Output: optimized in-place G-code
