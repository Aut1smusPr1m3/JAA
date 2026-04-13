# Ultra_Optimizer (JAA)

Ultra_Optimizer is a G-code post-processing pipeline designed for OrcaSlicer workflows.

It helps you improve print-path behavior without changing your slicer profile manually each time. The project focuses on three things:

- safer and more consistent motion behavior,
- optional surface-aware non-planar adjustments,
- optional output compaction through arc conversion.

Current release target: `v2.2`.

## What this project does

Ultra_Optimizer reads your slicer-generated `.gcode`, processes it in stages, and writes optimized output while preserving machine start/end sections.

At a high level:

1. Stage 1 always runs and applies kinematic acceleration shaping (M204 behavior) in the printable object window.
2. Stage 2 runs only when STL context and Open3D/GCodeZAA are available, adding surface-aware logic (including non-planar ironing support).
3. Stage 3 runs only when `ArcWelder.exe` is available, converting eligible linear segments into arcs where possible.

## How the mechanism works

### Stage 1: Window-aware kinematic optimization

- Detects printable object window boundaries using marker precedence.
- Leaves machine start/end blocks unchanged.
- Applies motion/acceleration strategy to printable content only.
- Deduplicates redundant feedrate-only modal `G0/G1 F...` commands in the printable window to reduce command noise.

### Stage 2: STL-informed surface processing (optional)

- Loads STL model data from `stl_models/`.
- Resolves object transform using metadata priority:
	- explicit `ZAA_OBJECT_POSITION` / `ZAA_OBJECT_ROTATION_DEG` hints,
	- slicer `EXCLUDE_OBJECT_DEFINE CENTER=/ROTATION=` metadata,
	- inferred printable-window bounds,
	- origin fallback.
- Performs raycast-backed height/contour analysis for qualifying extrusion moves.
- Emits sidecar metadata and integrity hashes for observability.

### Stage 3: Arc compression (optional)

- Calls `ArcWelder.exe` if present in repository root.
- Compresses suitable G1 paths into G2/G3 arcs.
- Produces a smaller and cleaner final motion stream for compatible firmware.

## Safety model

Safety behavior is treated as non-negotiable:

- build-plate floor enforced (`Z >= 0.0`),
- smoothing safety limits capped by config constraints,
- machine start/end G-code preserved unchanged,
- fallback/default behavior logged for post-run diagnosis.

## Quick start

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional Stage 2 runtime stack:

```bash
pip install -r requirements-optional.txt
```

### Windows (AIO bootstrap)

```powershell
./scripts/windows/bootstrap.ps1 -InstallDev
```

Optional strict GPU capability requirement during install:

```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -RequireSyclGpu
```

Optional GUI bootstrap launcher:

```powershell
python scripts/windows/bootstrap_gui.py
```

## Run the optimizer

```bash
python Ultra_Optimizer.py path/to/input.gcode
```

## Validate your setup

```bash
python -m pytest -q
```

## Critical setup warnings

- Run Ultra_Optimizer from the correct virtual environment used by OrcaSlicer post-processing.
- Enable verbose G-code comments in OrcaSlicer.
- Disable Arc fitting in OrcaSlicer so arc conversion is controlled by Stage 3.
- Provide transform metadata for moved/rotated objects when possible.
- Tune `MAX_SMOOTHING_ANGLE` for your printer and nozzle/duct clearance.

## Performance and GPU acceleration

Useful Stage 2 tuning environment variables:

```bash
# Coarser sampling (higher value is faster)
export GCODEZAA_SAMPLE_DISTANCE_MM=0.25

# Max points sampled per segment
export GCODEZAA_MAX_SEGMENT_SAMPLES=128

# Raycast batch size
export GCODEZAA_BATCH_RAY_SIZE=8192

# Device routing: auto|cpu:0|sycl:0
export GCODEZAA_RAYCAST_DEVICE=auto

# Fail if GPU acceleration is required but unavailable
export GCODEZAA_REQUIRE_GPU=0

# Optional profiler output
export ULTRA_OPTIMIZER_PROFILE=1
```

For GPU acceleration, use an Open3D build/runtime with SYCL support and available SYCL GPU devices.

Open3D SYCL installation guidance summary:
- official prebuilt SYCL Python wheels are Linux-focused (Ubuntu 22.04+),
- use the helper installer: `bash scripts/linux/install_open3d_sycl.sh`,
- install correct GPU drivers/runtime,
- for Intel GPU raycasting, install `intel-level-zero-gpu-raytracing`.

## Documentation map

- Start here: [docs/00-start-here.md](docs/00-start-here.md)
- Quickstart: [docs/01-user-guides/quickstart.md](docs/01-user-guides/quickstart.md)
- Installation: [docs/01-user-guides/installation.md](docs/01-user-guides/installation.md)
- Windows AIO: [docs/01-user-guides/windows-aio-setup.md](docs/01-user-guides/windows-aio-setup.md)
- OrcaSlicer integration: [docs/01-user-guides/orcaslicer-integration.md](docs/01-user-guides/orcaslicer-integration.md)
- Troubleshooting: [docs/01-user-guides/troubleshooting.md](docs/01-user-guides/troubleshooting.md)
- Pipeline reference: [docs/02-technical-reference/pipeline-stages.md](docs/02-technical-reference/pipeline-stages.md)
- Architecture map: [docs/02-technical-reference/architecture-map.md](docs/02-technical-reference/architecture-map.md)
- FAQ: [docs/04-reference/faq.md](docs/04-reference/faq.md)

## Repository structure (core)

- `Ultra_Optimizer.py`: main orchestrator (Stage 1 + Stage 2/3 handoff)
- `GCodeZAA/gcodezaa/process.py`: Stage 2 processing pipeline
- `GCodeZAA/gcodezaa/surface_analysis.py`: raycast/surface analysis helpers
- `scripts/windows/bootstrap.ps1`: Windows bootstrap installer
- `scripts/windows/bootstrap_gui.py`: GUI wrapper for bootstrap installer
- `test_*.py`: regression and behavior tests

## License

This project is distributed under GPL-3.0 terms. See `LICENSE` and the dependency inventory in [docs/04-reference/dependency-licenses.md](docs/04-reference/dependency-licenses.md).
