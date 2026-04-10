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

## Operational toggles
- `ENABLE_ARC_ANALYSIS`
- `GCODEZAA_AVAILABLE` (runtime import detection)
