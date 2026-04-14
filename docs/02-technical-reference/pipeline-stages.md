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
	`resolve_stage2_object_transform`, stores that result in a canonical `Stage2ObjectTransform` record,
	then either passes a legacy single `plate_object=(name, center_x, center_y, rotation_deg)` tuple or
	a validated list of per-object specs `(object_name, model_name, center_x, center_y, rotation_deg)` to Stage 2.
- Inside `gcodezaa.process.process_gcode`, the execution layer now also supports a backward-compatible
	list-based `PlateObjectSpec` contract so multiple preloaded objects can be mapped into the existing
	`EXCLUDE_OBJECT_START/END` switch path without breaking the legacy single-tuple call style.
- Transform resolution priority:
	1. explicit G-code comment hints (`ZAA_OBJECT_POSITION` / `ZAA_OBJECT_ROTATION_DEG`),
	2. unambiguous normalized object metadata with declared center and optional rotation,
	3. unambiguous normalized object metadata with polygon-derived center and optional declared rotation,
	4. unambiguous normalized object metadata with object-window-derived center and optional declared rotation,
	5. inferred printable-window motion bounds,
	6. fallback origin (0, 0) with 0° rotation.
- Normalization covers `EXCLUDE_OBJECT_DEFINE`, `EXCLUDE_OBJECT_START`, `EXCLUDE_OBJECT_END`,
	`POLYGON`, and Marlin-style `M486` markers.
- The resolver only applies normalized object metadata when selection is defensible. If multiple
	object records remain plausible, Stage 2 records the ambiguity in transform notes and falls back
	to motion-derived printable-window bounds instead of choosing the first object definition.
- When a defensible object candidate has no declared `CENTER` but does have `POLYGON`, Stage 2
	derives center from the polygon centroid before considering motion-derived bounds.
- When a defensible object candidate has no declared `CENTER` but does have an active span
	(`EXCLUDE_OBJECT_START/END` or `M486`), Stage 2 infers that candidate's center from motion only
	inside the object's own window and records `center-from-object-window` in transform notes.
- If explicit comment hints provide center but not rotation, normalized object metadata can still
	backfill rotation when there is a single defensible object candidate.
- Public multi-object handoff is now guarded rather than unconditional: batching only proceeds when
	candidates have defensible scores, non-overlapping object windows, resolved bounds with clearance,
	and unambiguous STL-model mapping from the current `stl_models/` inventory.
- Runtime warnings are emitted when rotation or center cannot be resolved explicitly.

Responsibilities:
- printable window processing with machine start/end passthrough,
- surface analysis and Z adjustments,
- non-planar ironing logic,
- optional STL Z-axis rotation before translation when transform metadata includes rotation,
- active-object switching via `EXCLUDE_OBJECT_START/END` when multiple scenes are preloaded.

Placement semantics:
- Stage 2 rotates meshes around the current mesh bounding-box center.
- After rotation, Stage 2 translates meshes so the current bounding-box center lands on the requested XY target.
- Z placement anchors the current mesh minimum Z to build-plate zero.
- `SurfaceAnalyzer` state is reset whenever the active object scene changes so smoothing and ray caches do not leak across arranged-plate object boundaries.

Sidecar behavior:
- Stage 2 writes sidecar metadata with hashes.
- Sidecar stores `stage2_object_transform` (resolved center, rotation, source, metadata family, window, inferred bounds, and notes when available).
- Sidecar stores `stage2_execution_contract` with the current public handoff mode, internal dispatch contract, placement semantics, and selected plate-object specs.
- `stage2_execution_contract.validation_notes` records why batching succeeded, used fuzzy STL-name resolution, or safely fell back to single-object mode.
- Sidecar stores `stage2_object_metadata_candidates` when normalized `EXCLUDE_OBJECT_*` or `M486` object records are discovered.
- Sidecar also stores `stage2_object_transform_schema_version`, `stage2_execution_contract_schema_version`, Stage 2 runtime env snapshot, and Stage 2 elapsed seconds for observability.
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
