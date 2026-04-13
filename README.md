# Ultra_Optimizer

Ultra_Optimizer is an OrcaSlicer-focused G-code post-processor with a three-stage pipeline:

1. Stage 1 (always): kinematic optimization and M204 acceleration control.
2. Stage 2 (optional): GCodeZAA surface-aware processing when STL models are available.
3. Stage 3 (optional): ArcWelder arc compression when ArcWelder.exe is present.

Machine start/end safety:
- Start G-code and end G-code are preserved unchanged.
- Stage 1 and Stage 2 operate only inside detected printable object windows.

## Start here
- [Documentation entry](docs/00-start-here.md)
- [5-minute quickstart](docs/01-user-guides/quickstart.md)
- [Installation](docs/01-user-guides/installation.md)
- [Windows AIO setup](docs/01-user-guides/windows-aio-setup.md)
- [OrcaSlicer integration](docs/01-user-guides/orcaslicer-integration.md)
- [Troubleshooting](docs/01-user-guides/troubleshooting.md)
- [Pipeline reference](docs/02-technical-reference/pipeline-stages.md)

## Quick setup
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional full Stage 2 dependencies:
```bash
pip install -r requirements-optional.txt
```

Windows all-in-one bootstrap:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev
```

## Test
```bash
python -m pytest -q
```

## Critical warnings
- Run the script from the correct project virtual environment. If OrcaSlicer calls a different Python interpreter, dependencies can be missing and Stage 2 can silently degrade/skip.
- In OrcaSlicer, enable verbose G-code comments. Feature/comment markers are required for reliable detection of ironing and feature transitions.
- In OrcaSlicer, disable Arc fitting. Arc conversion should be handled by the pipeline (Stage 3 / ArcWelder), not by the slicer.
- For moved/rotated objects, ensure transform metadata is available to Stage 2 (comment hints or `EXCLUDE_OBJECT_DEFINE` fields). Missing rotation metadata defaults to `0deg` and can misalign surface mapping.
- Set `MAX_SMOOTHING_ANGLE` for your printer's clearance limits. Default is conservative (`15deg`, hard-capped at `20deg`) but should still be validated for your nozzle/duct geometry.

## Performance tuning
If Stage 2 raycasting is too slow on large files, tune sampling and profiling with env vars:

```bash
# Coarser sampling (higher is faster): default 0.2
export GCODEZAA_SAMPLE_DISTANCE_MM=0.25

# Hard cap of samples per segment (default 384)
export GCODEZAA_MAX_SEGMENT_SAMPLES=128

# Optional sanity guard for implausible XY jumps (default 1000mm)
export GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM=1000

# Batch size for ray submissions (default 4096)
export GCODEZAA_BATCH_RAY_SIZE=8192

# Device selection: auto|cpu:0|sycl:0 (CUDA maps to SYCL when available)
export GCODEZAA_RAYCAST_DEVICE=auto

# Optional strict mode: fail if GPU is required but unavailable
export GCODEZAA_REQUIRE_GPU=0

# Optional pipeline profiling
export ULTRA_OPTIMIZER_PROFILE=1
python Ultra_Optimizer.py input.gcode
```

Profiling output defaults to `ultra_optimizer_profile.prof` in repo root and can be opened with tools like `snakeviz`.
For GPU acceleration, use an Open3D build/runtime with SYCL support and available SYCL GPU devices.

Runtime notes:
- Stage 2 logs an env snapshot (`[GCodeZAA] Stage 2 runtime env: ...`) for diagnostics.
- Raycast resolver logs selected device (`AUTO -> SYCL:0` or `AUTO -> CPU:0`).
- `GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM` is safety-clamped to `10..5000` mm to avoid masking state-jump defects.

## Notes
- Open3D is optional for advanced Stage 2 raycasting workflows.
- ArcWelder integration requires ArcWelder.exe in repository root.
- Runtime logs are written to `kinematic_engine.log`.
- Smoothing safety is conservative by default: `15deg` from vertical, hard-capped at `20deg`.
- `MAX_SMOOTHING_ANGLE` is defined by `DEFAULT_MAX_SMOOTHING_ANGLE` in `GCodeZAA/gcodezaa/config.py`.
