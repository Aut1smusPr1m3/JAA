# Pipeline Stages

## Stage 1 (always)
Implemented in `Ultra_Optimizer.py`.

Responsibilities:
- parse G0/G1/G2/G3 moves,
- inject M204 acceleration commands with hysteresis,
- preserve machine start/end G-code while applying kinematic acceleration strategy inside the printable window.

Printable window detection precedence:
1. `; EXECUTABLE_BLOCK_START` / `; EXECUTABLE_BLOCK_END`
2. first `; printing object ...` to last `; stop printing object ...`
3. full file fallback (if no markers exist)

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
- `Ultra_Optimizer.py` selects a primary STL, resolves object transform (center + rotation) via
	`resolve_stage2_object_transform`, and passes `plate_object=(name, center_x, center_y, rotation_deg)`.
- Transform resolution priority:
	1. explicit G-code comment hints (`ZAA_OBJECT_POSITION` / `ZAA_OBJECT_ROTATION_DEG`),
	2. `EXCLUDE_OBJECT_DEFINE CENTER=/ROTATION=` metadata,
	3. inferred printable-window motion bounds,
	4. fallback origin (0, 0) with 0° rotation.
- Runtime warnings are emitted when rotation or center cannot be resolved explicitly.

Responsibilities:
- printable window processing with machine start/end passthrough,
- surface analysis and Z adjustments,
- non-planar ironing logic,
- optional STL Z-axis rotation before translation when transform metadata includes rotation.

Sidecar behavior:
- Stage 2 writes sidecar metadata with hashes.
- Sidecar stores `stage2_object_transform` (resolved center, rotation, source, window, inferred bounds when available).
- Sidecar metadata is validated for schema/hash correctness.
- Final validation uses Stage 3 hash semantics when the output file has been mutated after Stage 2.

Operator guidance:
- For moved/rotated models, prefer explicit transform metadata in G-code comments or slicer-emitted `EXCLUDE_OBJECT_DEFINE` values to avoid fallback ambiguity.

## Stage 3 (optional)
Implemented in `Ultra_Optimizer.py` via external `ArcWelder.exe`.

Responsibilities:
- arc compression (G1 -> G2/G3 where possible),
- output compaction.

Important:
- ArcWelder output does not preserve slicer comments.
