# Transform Implementation Spec

This document translates the overhaul roadmap into concrete code-level changes for the first implementation milestones.

## Immediate milestone scope

Milestone 1 covers two things only:

- observability groundwork for Stage 2 and sidecar metadata
- transform-schema groundwork that introduces a canonical record without changing the existing runtime behavior materially

This milestone is intentionally conservative. It should improve structure and diagnosis before any multi-object or inference redesign lands.

## Current touch points

Primary code surfaces:

- `Ultra_Optimizer.py`
  - `detect_machine_print_window()`
  - `_parse_exclude_object_define_args()`
  - `_extract_transform_hints_from_gcode()`
  - `_infer_xy_center_from_gcode_window()`
  - `resolve_stage2_object_transform()`
  - `build_stage2_metadata()`
  - `validate_sidecar_metadata()`
  - main pipeline block around Stage 2 dispatch

- `GCodeZAA/gcodezaa/process.py`
  - `load_object()`
  - `process_gcode()`

Primary tests:

- `test_ultra_optimizer_stage2.py`
- `test_machine_gcode_window.py`
- `test_gcodezaa_processing.py`
- `test_gcodezaa_throughput.py`

## Proposed data structure changes

### 1. Canonical Stage 2 transform record

Add a dataclass in `Ultra_Optimizer.py` for the current single-object transform result.

Proposed shape:

```python
@dataclass(frozen=True)
class Stage2ObjectTransform:
    center_x: float
    center_y: float
    rotation_deg: float
    source: str
    window_start: int
    window_end: int
    inferred_bounds: dict | None
    metadata_family: str
    notes: tuple[str, ...] = ()

    def as_metadata_dict(self) -> dict:
        ...

    def as_plate_object(self, model_name: str) -> tuple[str, float, float, float]:
        ...
```

Rationale:

- preserve the current single-object behavior
- create a stable schema boundary for later multi-object redesign
- avoid spreading anonymous dict semantics further through the codebase

### 2. Metadata family field

The current `source` field is not enough for future normalization work. Introduce `metadata_family` now so later work can distinguish:

- `comment-hint`
- `exclude-object`
- `inferred-window-bounds`
- `default-origin`

For Milestone 1 this may duplicate `source`, which is acceptable. It creates a clean migration path for later normalization.

### 3. Sidecar transform schema marker

Extend `build_stage2_metadata()` so sidecar metadata includes:

- `stage2_object_transform_schema_version`
- `stage2_runtime_env_snapshot`
- `stage2_elapsed_seconds`

Keep `schema_version` unchanged for now to avoid conflating the overall sidecar schema with the transform sub-schema.

## Proposed function-level changes

### `resolve_stage2_object_transform()`

Current behavior:

- returns a plain dict
- chooses hint center, then inferred center, then origin
- always uses rotation hint if present, otherwise `0.0`

Milestone 1 change:

- return `Stage2ObjectTransform`
- preserve current center and rotation precedence exactly
- add `metadata_family`
- add optional notes when the transform is inferred or fully defaulted

Do not change inference semantics yet.

### `_extract_transform_hints_from_gcode()`

Milestone 1 change:

- keep current parsing behavior
- return enough source detail to support `metadata_family`
- remain tolerant of malformed `EXCLUDE_OBJECT_DEFINE` content

Do not attempt multi-object parsing in this milestone.

### `build_stage2_metadata()`

Milestone 1 change:

- accept either a dataclass instance or a dict for `stage2_object_transform`
- serialize the dataclass via `as_metadata_dict()`
- include transform schema version and Stage 2 observability fields

### Stage 2 pipeline dispatch in `Ultra_Optimizer.py`

Milestone 1 change:

- compute explicit `stage2_start_time`
- build a structured Stage 2 log summary showing:
  - selected model
  - center
  - rotation
  - source
  - metadata family
  - window span
  - inferred bounds if present
- write `stage2_elapsed_seconds` and runtime env snapshot to sidecar metadata
- keep `plate_object` tuple handoff unchanged via `Stage2ObjectTransform.as_plate_object()`

### `validate_sidecar_metadata()`

Milestone 1 change:

- continue validating existing required keys
- do not require new observability keys yet
- optionally validate that `stage2_object_transform` is a mapping if present

This keeps backward compatibility while groundwork is landing.

## Logging changes for Milestone 1

Add one concise Stage 2 provenance log line and one debug detail line.

Info-level summary:

```text
[GCodeZAA] Stage 2 transform: model=... center=(x,y) rotation=... source=... family=... window=start-end
```

Debug-level detail:

```text
[GCodeZAA] Stage 2 transform detail: inferred_bounds=... notes=...
```

Keep logs human-readable; no JSON logging is needed for this milestone.

## Explicit non-goals for this milestone

- multi-object transform resolution
- polygon-aware centroiding
- `M486` normalization
- rotation inference from toolpath geometry
- mesh registration or reconciliation
- changes to `GCodeZAA/gcodezaa/process.py` semantics

## Follow-on milestone hooks

This structure should make Milestone 2 easier by providing a stable place to add:

- object identity
- polygon data
- active object spans
- ambiguity flags beyond simple notes
- a list-based object model instead of a single transform record

## Expected code diff shape

- one small dataclass and two small helper methods in `Ultra_Optimizer.py`
- one updated `resolve_stage2_object_transform()` return type
- one modest `build_stage2_metadata()` expansion
- one Stage 2 logging improvement in the pipeline block
- a few tests updated or added in `test_ultra_optimizer_stage2.py`

This should remain a low-risk, schema-first change.