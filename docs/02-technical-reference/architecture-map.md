# Architecture Map

This page documents module dependencies, runtime data flow, public API surface, and performance-critical paths.

## End-to-end data flow

```
OrcaSlicer output G-code
        |
        v
Ultra_Optimizer.py
  - window detection
  - Stage 1 kinematic optimization
        |
        +--> Stage 2 optional dispatch (GCodeZAA)
        |      - STL selection
        |      - transform resolution (canonical Stage2ObjectTransform)
        |      - conservative object metadata normalization and selection
        |      - guarded public single vs multi-object handoff
        |      - process_gcode(...)
        |      - sidecar metadata write/validate
        |
        +--> Stage 3 optional dispatch (ArcWelder.exe)
               - arc compression
               - sidecar stage3 status update
        |
        v
Final G-code (+ sidecar metadata where applicable)
```

## Conditional branches
- Stage 2 runs only when GCodeZAA is importable and STL input is available.
- Stage 2 may run on CPU fallback when SYCL GPU is unavailable.
- Stage 2 transform resolution fallback order:
  1. explicit comment hints,
  2. unambiguous normalized object metadata,
  3. unambiguous normalized object metadata with polygon-derived center,
  4. unambiguous normalized object metadata with per-object window-derived center,
  5. inferred window bounds,
  6. default origin/0deg.
- Stage 2 normalizes `EXCLUDE_OBJECT_START/END`, `POLYGON`, and `M486` markers into candidate object records.
- If a selected candidate has polygon metadata but no declared center, Stage 2 derives the transform center from the polygon centroid.
- If a selected candidate has no declared center, Stage 2 can now derive its center from motion inside that candidate's own active span.
- When multiple object records are plausible, the runtime records the ambiguity and falls back to inferred printable-window bounds rather than choosing an arbitrary metadata record.
- When multiple defensible candidates survive ranking, Stage 2 now attempts a guarded public multi-object handoff by matching candidate names against the current STL inventory. It falls back to single-object mode if model mapping is ambiguous, candidate windows overlap, or clearance checks fail.
- Stage 3 runs only when `ArcWelder.exe` exists.

## Printable window precedence
Window detection is explicitly ordered:
1. executable block markers,
2. printing object comment markers,
3. full-file fallback.

## Sidecar lifecycle
1. Stage 2 computes input hash and invalidates stale sidecar entries.
2. Stage 2 writes metadata with selected model, resolved transform, execution-contract evidence, normalized object metadata candidates, runtime env snapshot, and elapsed time.
3. Stage 2 validates sidecar schema and hash consistency.
4. Stage 3 updates sidecar status and output-hash context when applicable.
5. Final checks remove stale sidecar when output/hash drift is detected.

## Module dependency map

### Pipeline orchestration
- `Ultra_Optimizer.py`
  - Owns Stage 1 logic and process window enforcement.
  - Owns current single-object transform resolution and future-facing object metadata normalization scaffolding.
  - Calls `gcodezaa.process.process_gcode` for Stage 2.
  - Calls ArcWelder subprocess integration for Stage 3.
  - Owns sidecar hash/validation/update utilities.

### Stage 2 core
- `GCodeZAA/gcodezaa/process.py`
  - Builds `ProcessorContext`.
  - Creates/loads raycast scene via Open3D.
  - Runs per-line processing and extrusion/surface transforms.
  - Supports a backward-compatible list-based preloaded object contract that feeds the existing `EXCLUDE_OBJECT_START/END` switch path.
  - Applies build-plate clamp and safety guards.
- `GCodeZAA/gcodezaa/context.py`
  - Shared mutable state for parsing mode, geometry state, and active objects.
- `GCodeZAA/gcodezaa/surface_analysis.py`
  - `SurfaceAnalyzer` batched raycasting and normal/Z offset logic.
  - Segment length guard and adaptive sample strategy.

## Public API surface (`gcodezaa` package)
- CLI entry:
  - `gcodezaa.__main__.main()`
- Functional API:
  - `gcodezaa.process.process_gcode(gcode, model_dir, plate_object=None)`
- Lower-level helpers used by integration/tests:
  - `gcodezaa.process.detect_processing_window(...)`
  - `gcodezaa.process.resolve_raycast_device_spec()`
  - `gcodezaa.process.load_object(...)`

## Performance-critical paths
- Stage 2 per-segment sampling loop and raycast batch submission.
- `SurfaceAnalyzer.batch_analyze_points()` tensor cast path.
- Long-segment sample count behavior controlled by:
  - `GCODEZAA_SAMPLE_DISTANCE_MM`
  - `GCODEZAA_MAX_SEGMENT_SAMPLES`
  - `GCODEZAA_BATCH_RAY_SIZE`
  - `GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM`

## Observability points
- Stage 2 logs runtime env snapshot and selected raycast device.
- Transform resolution logs include center, rotation, and source.
- Transform resolution logs now also include metadata family, window span, inferred bounds, normalized object metadata candidates when present, and schema-backed sidecar fields.
- Sidecar execution evidence now records the public handoff mode, internal dispatch contract, placement semantics, and selected plate-object specs.
- Sidecar validation notes now also capture guarded multi-object decisions such as fuzzy STL-name matches and safe single-object fallbacks.
- Stage 2 placement semantics are now explicit and tested: rotation uses the mesh bounding-box center, XY translation uses the post-rotation bounding-box center, and Z anchors mesh minimum Z to build-plate zero.
- Transform notes capture selection provenance such as `selected-object:<name>`, ambiguity, and metadata-backed rotation fallback.
- Transform notes also capture `center-from-object-polygon` when polygon metadata supplied the applied center.
- Transform notes also capture `center-from-object-window` when the selected object had to be centered from its own motion span.
- Fallback/warning events are explicit when transform metadata is missing.
