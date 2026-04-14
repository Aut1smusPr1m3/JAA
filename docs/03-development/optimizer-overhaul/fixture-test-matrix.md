# Validation Fixture and Test Matrix

This document turns the rollout plan into a concrete test and fixture matrix aligned with the current repository test files.

## Fixture classes

### A. Window and metadata fixtures

Purpose:

- validate window precedence
- validate transform metadata parsing
- validate fallback behavior

Representative cases:

1. executable block markers only
2. printing-object comments only
3. explicit `ZAA_OBJECT_POSITION` plus `ZAA_OBJECT_ROTATION_DEG`
4. single `EXCLUDE_OBJECT_DEFINE CENTER=... ROTATION=...`
5. no metadata, inferred printable-window bounds only
6. no usable metadata, default-origin fallback

Primary files:

- `test_machine_gcode_window.py`
- `test_ultra_optimizer_stage2.py`

### B. Motion-state fixtures

Purpose:

- validate transform inference under motion-mode changes

Representative cases:

1. `G90` absolute positioning
2. `G91` relative positioning
3. `G92` resets before and during printable window
4. arc commands in context priming

Primary files:

- `test_ultra_optimizer_stage2.py`
- `test_gcodezaa_processing.py`

### C. Stage 2 metadata and sidecar fixtures

Purpose:

- validate canonical transform serialization
- validate sidecar observability fields
- validate hash lifecycle

Representative cases:

1. sidecar round-trip with transform record
2. stale sidecar invalidation on input hash change
3. sidecar Stage 3 status update preserving Stage 2 fields
4. sidecar validation with optional transform observability fields present
5. sidecar execution-contract evidence for selected plate-object specs and placement semantics

Primary files:

- `test_ultra_optimizer_stage2.py`

### D. Throughput and diagnostic fixtures

Purpose:

- validate low-risk performance-related behavior and diagnostics

Representative cases:

1. non-extrusion moves skip Stage 2 surface following
2. long segments hit sample caps
3. implausible segments are skipped with warning context
4. runtime env snapshot remains stable

Primary files:

- `test_gcodezaa_throughput.py`
- `test_ultra_optimizer_stage2.py`

### E. Future multi-object fixtures

Purpose:

- prepare for Milestone 2 and beyond

Representative cases:

1. multiple `EXCLUDE_OBJECT_DEFINE` records in one file
2. distinct object windows across the same file
3. crowded arranged plate where center-only reasoning is ambiguous
4. `M486`-like object markers requiring normalization

The execution-contract groundwork for these fixtures is now implemented in `test_gcodezaa_processing.py`, but broader public multi-object dispatch from `Ultra_Optimizer.py` is still pending.

## Test mapping by existing file

### `test_machine_gcode_window.py`

Current coverage:

- executable block precedence
- printing-object comment windows
- machine start and end passthrough
- feedrate dedup behavior

Add next:

- default full-file fallback case if not already present in a stronger form
- future multi-object window extraction cases

### `test_ultra_optimizer_stage2.py`

Current coverage:

- STL model selection
- Stage 2 env snapshot
- metadata build and sidecar lifecycle
- transform center inference
- comment-hint and `EXCLUDE_OBJECT_DEFINE` transform resolution
- repeated-span scoring and ranked-candidate serialization
- execution-contract sidecar evidence for selected plate-object specs and placement semantics

Add in Milestone 1:

- dataclass-backed transform serialization remains stable
- `metadata_family` field present in serialized transform metadata
- `stage2_object_transform_schema_version` present
- `stage2_runtime_env_snapshot` and `stage2_elapsed_seconds` stored when provided

Add next:

- polygon-vs-motion mismatch evidence once reconciliation penalties land
- sidecar assertions for future public multi-object handoff data

### `test_gcodezaa_processing.py`

Current coverage:

- processing with and without slicer headers
- arc preservation
- line-type detection
- context priming across `G90`, `G91`, `G92`
- explicit mesh pivot and translation semantics
- backward-compatible list-based plate object contract
- arranged-plate object switching, preloaded object reuse, and analyzer resets across object boundaries

Add next:

- additional priming cases that mirror transform inference expectations
- broader arranged-plate fixtures that include non-planar ironing and mixed metadata families in the same file

### `test_gcodezaa_throughput.py`

Current coverage:

- non-extrusion skip path
- sample cap behavior
- implausible segment skip path
- state-jump diagnostic logs

Add next:

- ensure new observability additions do not break throughput guard expectations
- benchmark-oriented smoke cases for new Stage 2 telemetry

## Benchmark fixture matrix

Non-pytest evidence fixtures should include:

1. a standard benchy-style file for baseline timing
2. a moved and rotated object with explicit hints
3. a metadata-poor inference-only file
4. a long-segment stress file
5. a no-STL optional-skip file

Use:

- `scripts/perf/profile_benchy.sh`
- `scripts/perf/capture_stage2_evidence.sh`

## Acceptance criteria for Milestone 1

Milestone 1 is complete when:

1. transform results are produced through a canonical record in code
2. current transform behavior is unchanged for existing fixtures
3. sidecar metadata can include transform schema and Stage 2 observability fields
4. existing Stage 2 tests still pass
5. at least one new test asserts the transform schema groundwork explicitly

## Notes on sequencing

- The matrix intentionally keeps Milestone 1 focused on structure and diagnosis.
- Multi-object and normalization-heavy cases are listed now so fixture design does not lag behind implementation later.
- The current repository has moved beyond the original Milestone 1 scope; the next unlanded fixture work is public multi-object handoff plus polygon-vs-motion reconciliation rather than basic contract scaffolding.
- Any fixture added for future `M486` or polygon-aware work should be minimal and isolated so it does not confuse the current single-object test surface.