# Pipeline Stages

## Stage 1 (always)
Implemented in `Ultra_Optimizer.py`.

Responsibilities:
- parse G0/G1/G2/G3 moves,
- inject M204 acceleration commands with hysteresis,
- preserve line/comments while applying kinematic acceleration strategy.

Notes:
- Stage 1 is intentionally kinematic-only.
- surface contouring/raycasting is delegated to Stage 2.

## Stage 2 (optional)
Implemented by `gcodezaa.process.process_gcode`.

Execution conditions:
- GCodeZAA importable,
- `stl_models/` exists,
- at least one `.stl` present.

Current handoff:
- `Ultra_Optimizer.py` now selects a primary STL and passes `plate_object=(name,0.0,0.0)`.

Responsibilities:
- executable block processing,
- surface analysis and Z adjustments,
- non-planar ironing logic.

## Stage 3 (optional)
Implemented in `Ultra_Optimizer.py` via external `ArcWelder.exe`.

Responsibilities:
- arc compression (G1 -> G2/G3 where possible),
- output compaction.

Important:
- ArcWelder output does not preserve slicer comments.
