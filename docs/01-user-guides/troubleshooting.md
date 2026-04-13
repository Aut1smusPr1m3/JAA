# Troubleshooting

## No visible Z smoothing
Check:
1. `stl_models/` contains at least one `.stl` file.
2. Stage 2 logs show selected STL model.
3. GCodeZAA import succeeded in logs.

## Surface mapping looks offset after moving/rotating the model
Check:
1. Stage 2 log line includes expected center/rotation and transform source.
2. If rotation in log is `0.000deg` for a rotated model, provide explicit metadata.
3. Add G-code hints near the top of the file and re-run:

```gcode
; ZAA_OBJECT_POSITION: 110.25,128.50
; ZAA_OBJECT_ROTATION_DEG: 37.5
```

4. If your slicer emits `EXCLUDE_OBJECT_DEFINE`, verify it includes `CENTER=...` and optional rotation (`ROTATION`, `ROTATION_DEG`, `ANGLE`, or `ANGLE_DEG`).

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

## Windows bootstrap fails before completion
Common signatures and fixes:
1. `No compatible Python launcher found. Install Python 3.11 or 3.12 first.`
: Install Python 3.11/3.12 and restart shell.
2. `ArcWelder.exe not found. Provide -ArcWelderPath or -ArcWelderUrl.`
: Re-run bootstrap with one ArcWelder source argument.
3. `ArcWelderPath does not exist: ...`
: Correct the local path or permissions.
4. `Virtual environment python not found: ...`
: Remove the broken venv directory and re-run bootstrap.
5. `SYCL GPU check failed. Use Open3D SYCL setup guidance (Linux x86_64 wheel/runtime or custom build), install correct GPU drivers, and ensure at least one SYCL GPU device is available.`
: For official prebuilt SYCL wheel flow, run `bash scripts/linux/install_open3d_sycl.sh` on Linux. On Windows, use strict mode only when you have a custom SYCL-capable Open3D runtime.

Quick reference:
- [Windows AIO setup](windows-aio-setup.md)

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
4. `stage2_object_transform` in sidecar matches your intended placement and rotation.

## Stage 2 is very slow / high CPU
Use throughput controls:
1. Increase sample spacing (fewer rays): `GCODEZAA_SAMPLE_DISTANCE_MM=0.25`
2. Lower segment sample cap: `GCODEZAA_MAX_SEGMENT_SAMPLES=128`
3. Increase batch size for cast submission: `GCODEZAA_BATCH_RAY_SIZE=8192`
4. Guard unrealistic jumps in surface-following segments: `GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM=1000`

Notes:
- `GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM` is safety-clamped to `10..5000` mm at runtime.
- Values above `5000` mm are reduced to `5000` mm with a warning to avoid masking state-jump defects.
- Values below `10` mm are raised to `10` mm to avoid excessive false positives.

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

Open3D upstream note:
- prebuilt SYCL Python wheels are Linux-focused (Ubuntu 22.04+),
- for Intel GPU raycasting, install `intel-level-zero-gpu-raytracing`.

Expected diagnostics in logs:
1. Stage 2 prints runtime env snapshot: `[GCodeZAA] Stage 2 runtime env: ...`.
2. Device resolver prints selection: `Raycast device resolved: AUTO -> SYCL:0` or `AUTO -> CPU:0`.
3. Explicit requests print selection/fallback messages (`SYCL:0` or `CPU:0`).

Quick SYCL check:
```bash
python -c "import open3d as o3d; print(o3d.core.sycl.get_available_devices() if hasattr(o3d.core, 'sycl') else 'SYCL not available'); print('SYCL:0 available=', o3d.core.sycl.is_available(o3d.core.Device('SYCL:0')) if hasattr(o3d.core, 'sycl') else False)"
```

## Implausible segment distance logs
Interpretation:
1. `Skipping surface-following for implausible segment ...` means guard triggered (segment exceeded configured max).
2. `Segment sampling capped ...` means segment is considered plausible but sample count hit cap.

If you still see very large capped distances:
1. Verify you are running latest branch/code.
2. Check Stage 2 env snapshot for `GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM` overrides.
3. Keep `GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM` near default unless actively debugging.

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

## Related guides
- [OrcaSlicer integration](orcaslicer-integration.md)
- [Pipeline stages reference](../02-technical-reference/pipeline-stages.md)
- [FAQ](../04-reference/faq.md)
- [Windows AIO setup](windows-aio-setup.md)
