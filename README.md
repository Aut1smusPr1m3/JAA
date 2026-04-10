# Ultra_Optimizer

Ultra_Optimizer is an OrcaSlicer-focused G-code post-processor with a three-stage pipeline:

1. Stage 1 (always): kinematic optimization and M204 acceleration control.
2. Stage 2 (optional): GCodeZAA surface-aware processing when STL models are available.
3. Stage 3 (optional): ArcWelder arc compression when ArcWelder.exe is present.

## Start here
- [Documentation entry](docs/00-start-here.md)
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

## Performance tuning
If Stage 2 raycasting is too slow on large files, tune sampling and profiling with env vars:

```bash
# Coarser sampling (higher is faster): default 0.2
export GCODEZAA_SAMPLE_DISTANCE_MM=0.25

# Hard cap of samples per segment (default 192)
export GCODEZAA_MAX_SEGMENT_SAMPLES=128

# Batch size for ray submissions (default 4096)
export GCODEZAA_BATCH_RAY_SIZE=8192

# Optional pipeline profiling
export ULTRA_OPTIMIZER_PROFILE=1
python Ultra_Optimizer.py input.gcode
```

Profiling output defaults to `ultra_optimizer_profile.prof` in repo root and can be opened with tools like `snakeviz`.

## Notes
- Open3D is optional for advanced Stage 2 raycasting workflows.
- ArcWelder integration requires ArcWelder.exe in repository root.
- Runtime logs are written to `kinematic_engine.log`.
