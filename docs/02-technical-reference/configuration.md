# Configuration

## Core kinematic settings (`Ultra_Optimizer.py`)
- `MAX_ACCEL_XY`
- `MAX_ACCEL_Z`
- `MIN_ACCEL`
- `ACCEL_HYSTERESIS`

## Arc settings
- `AW_DYNAMIC_RES`
- `AW_MAX_ERROR`
- `AW_TOLERANCE`

## ZAA settings
- `ZAA_MAX_SMOOTHING_ANGLE` defaults to `15.0` degrees from vertical.
- A hard safety cap (`20.0`) limits accidental over-smoothing configuration.
- Stage 1 does not perform heuristic Z-AA; only Stage 2 true surface following applies Z offsets.
- Stage 2 behavior depends on GCodeZAA/Open3D availability and STL presence.

### MAX_SMOOTHING_ANGLE tuning
- Source setting: `DEFAULT_MAX_SMOOTHING_ANGLE` in `GCodeZAA/gcodezaa/config.py`.
- Runtime effective value: `ZAA_MAX_SMOOTHING_ANGLE = min(DEFAULT_MAX_SMOOTHING_ANGLE, 20.0)`.
- Recommendation: start at `15deg` and tune conservatively based on nozzle/cooling-duct clearance on your printer.
- Warning: larger values can increase collision risk on steep local geometry.

## Operational toggles
- `ENABLE_ARC_ANALYSIS`
- `GCODEZAA_AVAILABLE` (runtime import detection)

## Stage 2 runtime environment controls
- `GCODEZAA_RAYCAST_DEVICE`
	- Default: `auto`
	- Values: `auto`, `sycl:0`, `cpu:0` (and `cuda` alias mapped to `sycl:0`)
- `GCODEZAA_REQUIRE_GPU`
	- Default: `0`
	- If `1`, Stage 2 raises when requested GPU path is unavailable.
- `GCODEZAA_SAMPLE_DISTANCE_MM`
	- Default: `0.2`
- `GCODEZAA_MAX_SEGMENT_SAMPLES`
	- Default: `384`
- `GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM`
	- Default: `1000`
	- Runtime clamp: `10..5000` mm (out-of-range values are clamped with warning logs)
- `GCODEZAA_BATCH_RAY_SIZE`
	- Default: `4096`

## Runtime observability
- Stage 2 emits one environment snapshot log at startup (`[GCodeZAA] Stage 2 runtime env: ...`).
- Raycast device resolver emits resolved selection info (for example `AUTO -> SYCL:0` or `AUTO -> CPU:0`).
