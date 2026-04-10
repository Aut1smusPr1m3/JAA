# Troubleshooting

## No visible Z smoothing
Check:
1. `stl_models/` contains at least one `.stl` file.
2. Stage 2 logs show selected STL model.
3. GCodeZAA import succeeded in logs.

## Ironing not behaving as expected
Check:
1. OrcaSlicer `Verbose G-code` is enabled so `; FEATURE:` and inline `; ironing` comments are preserved.
2. Stage 2 actually executed (not skipped).
3. Output after Stage 3 may not keep comments (ArcWelder strips comments).

## Arc behavior is unexpected
Check:
1. OrcaSlicer `Arc fitting` is disabled.
2. Arc conversion is expected to happen in Stage 3 via ArcWelder.

## Wrong interpreter / missing modules at runtime
Check:
1. OrcaSlicer is using the same virtual environment interpreter as your validated setup.
2. Running `python Ultra_Optimizer.py input.gcode` from that venv succeeds.
3. Required dependencies in that venv are installed (`requirements.txt`, optional `requirements-optional.txt` if needed).

## Smoothing looks too aggressive or too weak
Check:
1. `DEFAULT_MAX_SMOOTHING_ANGLE` in `GCodeZAA/gcodezaa/config.py` matches your printer clearance constraints.
2. Remember the hard safety cap is `20deg`.
3. Re-run a supervised test print after changing the angle.

## Stage 2 skipped
Common reasons:
- GCodeZAA import failure
- missing `stl_models/` directory
- no `.stl` files in `stl_models/`

## Start or end machine G-code seems modified
Expected behavior:
- machine start and end blocks are passed through unchanged
- only printable window lines are processed

Window marker precedence:
1. `; EXECUTABLE_BLOCK_START` / `; EXECUTABLE_BLOCK_END`
2. first `; printing object ...` to last `; stop printing object ...`

If your slicer profile does not emit these markers, processing may fall back to full-file mode.

## Sidecar integrity warnings
If sidecar validation fails, check:
1. Stage 2 and Stage 3 actually completed in order.
2. Output file was not externally modified between stage writes.
3. Sidecar file (`.meta`) is present and parseable JSON.

## Stage 2 is very slow / high CPU
Use throughput controls:
1. Increase sample spacing (fewer rays): `GCODEZAA_SAMPLE_DISTANCE_MM=0.25`
2. Lower segment sample cap: `GCODEZAA_MAX_SEGMENT_SAMPLES=128`
3. Increase batch size for cast submission: `GCODEZAA_BATCH_RAY_SIZE=8192`
4. Guard unrealistic jumps in surface-following segments: `GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM=1000`

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

## GPU acceleration setup (SYCL)
Stage 2 raycasting device selection:
1. `GCODEZAA_RAYCAST_DEVICE=auto` (default): use SYCL GPU if available, else CPU.
2. `GCODEZAA_RAYCAST_DEVICE=sycl:0`: request SYCL path explicitly.
3. `GCODEZAA_RAYCAST_DEVICE=cpu:0`: force CPU for comparison/debug.

If you want a hard failure when no GPU is available:
```bash
GCODEZAA_REQUIRE_GPU=1 python Ultra_Optimizer.py input.gcode
```

If logs say SYCL GPU unavailable, ensure your Open3D runtime and system drivers expose SYCL devices.

Repeatable benchy throughput run:
```bash
./scripts/perf/profile_benchy.sh
```
This creates timestamped artifacts under `perf_runs/benchy/` including:
- processed G-code copy
- profiler output (`.prof`)
- optimizer log
- safety and timing summary

## ArcWelder skipped
Reason:
- `ArcWelder.exe` missing from repository root.

## Validate quickly
```bash
python -m pytest -q
```
