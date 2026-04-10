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
- `ZAA_MAX_SMOOTHING_ANGLE` is aligned to `40.0` across core modules.
- Stage 2 behavior depends on GCodeZAA/Open3D availability and STL presence.

## Operational toggles
- `ENABLE_ARC_ANALYSIS`
- `GCODEZAA_AVAILABLE` (runtime import detection)
