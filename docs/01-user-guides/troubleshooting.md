# Troubleshooting

## No visible Z smoothing
Check:
1. `stl_models/` contains at least one `.stl` file.
2. Stage 2 logs show selected STL model.
3. GCodeZAA import succeeded in logs.

## Ironing not behaving as expected
Check:
1. Input G-code contains slicer `;TYPE:` markers.
2. Stage 2 actually executed (not skipped).
3. Output after Stage 3 may not keep comments (ArcWelder strips comments).

## Stage 2 skipped
Common reasons:
- GCodeZAA import failure
- missing `stl_models/` directory
- no `.stl` files in `stl_models/`

## Stage 2 is very slow / high CPU
Use throughput controls:
1. Increase sample spacing (fewer rays): `GCODEZAA_SAMPLE_DISTANCE_MM=0.25`
2. Lower segment sample cap: `GCODEZAA_MAX_SEGMENT_SAMPLES=128`
3. Increase batch size for cast submission: `GCODEZAA_BATCH_RAY_SIZE=8192`

Example:
```bash
GCODEZAA_SAMPLE_DISTANCE_MM=0.25 \
GCODEZAA_MAX_SEGMENT_SAMPLES=128 \
python Ultra_Optimizer.py input.gcode
```

For deep diagnostics, enable built-in profiling:
```bash
ULTRA_OPTIMIZER_PROFILE=1 python Ultra_Optimizer.py input.gcode
```
This writes `ultra_optimizer_profile.prof` for analysis (e.g. with `snakeviz`).

## ArcWelder skipped
Reason:
- `ArcWelder.exe` missing from repository root.

## Validate quickly
```bash
python -m pytest -q
```
