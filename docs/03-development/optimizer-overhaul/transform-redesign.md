# Transform Redesign Plan

This document covers the redesign of object translation and rotation handling so the pipeline can infer placement more reliably and support full slicer-layout awareness.

## Current repository constraints

- `resolve_stage2_object_transform()` in `Ultra_Optimizer.py` currently resolves a single transform from hints, `EXCLUDE_OBJECT_DEFINE`, or printable-window bounds.
- Stage 2 `load_object()` in `GCodeZAA/gcodezaa/process.py` applies mesh rotation and translation for one selected object.
- Current tests mainly cover single-object center inference and hint parsing.

## Design goal

Replace the current single-transform fallback chain with an object-aware transform system that can:

- normalize inconsistent slicer metadata
- represent multiple objects and arranged plates
- infer translation and rotation with provenance
- degrade safely when metadata is incomplete or ambiguous
- feed Stage 2 with explicit, testable placement semantics

## Current implementation status

Implemented so far:

- canonical `Stage2ObjectTransform` result for Stage 2 handoff and sidecar persistence
- normalized object metadata extraction for `EXCLUDE_OBJECT_DEFINE`, `EXCLUDE_OBJECT_START`, `EXCLUDE_OBJECT_END`, and `M486`
- conservative runtime selection that only uses normalized object metadata when one candidate is defensible
- ambiguity fallback that prefers printable-window motion bounds over arbitrary object-definition selection
- polygon-centroid-based center recovery for a selected object when `POLYGON` is present but `CENTER` is missing
- per-object motion-derived center inference when a selected metadata candidate has an active object span but no declared `CENTER`
- repeated per-object spans preserved across arranged-plate files, with deterministic ranked-candidate scoring and sidecar persistence of ranking evidence
- explicit Stage 2 mesh-placement semantics: rotate around mesh bounding-box center, then translate the post-rotation bounding-box center to the requested XY target while anchoring mesh minimum Z to build-plate zero
- backward-compatible list-based Stage 2 dispatch contract in `gcodezaa.process.process_gcode()` that preloads multiple scenes while preserving the legacy single-tuple handoff
- arranged-plate execution regressions proving preloaded object reuse, active-object scene routing, and analyzer-state resets across `EXCLUDE_OBJECT_START/END` boundaries
- guarded public multi-object Stage 2 handoff from `Ultra_Optimizer.py` when ranked candidates have non-overlapping windows, resolved bounds with clearance, and unambiguous STL-model mapping
- polygon-vs-motion mismatch penalties for ranked candidates, plus sidecar validation notes that explain fuzzy model matches or safe single-object fallback decisions

Still pending:

- rotation inference without declared metadata
- richer model-name reconciliation for cases where slicer object names do not map cleanly onto the STL inventory
- mesh/toolpath reconciliation beyond current polygon-vs-motion penalties, especially for crowded ambiguous layouts

## Phase A: Canonical metadata model

Define a canonical object record with fields for:

- object identity and raw source name
- metadata source family: JAA hint, Klipper EXCLUDE_OBJECT, Marlin M486-derived, printing-object comments, inferred
- declared center
- declared polygon or bounds
- declared rotation
- start and end markers or window spans
- confidence and ambiguity flags
- final applied transform

This record should exist before any algorithm redesign so all later logic works against one schema.

## Phase B: Metadata normalization layer

Build a normalization plan for all upstream formats that may appear in real files:

1. JAA explicit hints
   - `ZAA_OBJECT_POSITION`
   - `ZAA_OBJECT_ROTATION_DEG`

2. Klipper-style object metadata
   - `EXCLUDE_OBJECT_DEFINE`
   - `EXCLUDE_OBJECT_START`
   - `EXCLUDE_OBJECT_END`
   - `CENTER`
   - `POLYGON`

3. Marlin-style `M486` sequences where present
   - map object identity and block boundaries
   - derive object bounds or polygons from motion if `DEFINE` metadata is absent

4. printing-object comment windows and fallback window markers

Research basis:

- Klipper explicitly expects preprocessing and documents `CENTER` and `POLYGON` as first-class object metadata.
- OrcaSlicer has known cases where Klipper-flavored output still emits Marlin-style `M486`, so normalization is required in practice.

## Phase C: Object window extraction

Redesign window detection so the system can represent:

- file-level process window
- per-object active spans
- incomplete spans with warnings
- arranged plates where objects appear across many layers

Important rule:

- do not collapse multi-object files to one inferred center unless no object-level evidence exists

## Phase D: Translation and rotation inference strategy

Use a tiered inference model:

1. explicit object position and rotation hints
2. normalized slicer object metadata
3. per-object motion-derived bounds and polygon summaries
4. optional mesh/toolpath reconciliation for ambiguous objects
5. visible fallback with confidence downgrade and warnings

Current runtime state:

- Steps 1 and 2 are implemented for the current selected transform, including repeated spans, ranked candidates, ambiguity fallback, and guarded public batching when candidate-to-STL mapping is defensible.
- Step 3 is implemented for defensible metadata candidates, and the execution layer now supports arranged-plate scene switching through preloaded `EXCLUDE_OBJECT_START/END` flows plus guarded public multi-object dispatch from `Ultra_Optimizer.py`.

### Rotation-specific strategy

- prefer declared rotation when available
- when not available, do not pretend motion bounds alone can fully identify rotation in every case
- if heuristic rotation inference is explored later, gate it behind confidence scoring and an opt-in path

### Translation-specific strategy

- infer per-object XY bounds from motion only inside that object's active spans
- incorporate polygon-derived centroids where available
- treat partial coverage and wipe moves as sources of bias that need explicit filtering

## Phase E: Mesh transform semantics in Stage 2

Before implementing automatic inference widely, settle these semantics:

- what point in mesh space is the canonical placement origin
- what point on the print bed is the canonical target
- whether rotation occurs around mesh centroid, declared object center, or another normalized pivot
- how Z anchoring works for objects with non-zero model bases or unusual mesh minima

This phase must produce deterministic rules and corresponding tests before performance work continues.

Current status:

- This phase is implemented for the current Stage 2 execution model.
- Tests now lock down pivot and translation behavior in `test_gcodezaa_processing.py`.
- Sidecar metadata now records the placement and dispatch contract explicitly.

## Phase F: Provenance and diagnostics

Every transform decision should preserve:

- chosen object
- source precedence chain
- raw upstream metadata
- inferred bounds or polygon summary
- ambiguity conditions
- final transform and pivot semantics

Persist this in sidecar metadata and logs so failures are diagnosable after the fact.

Current status:

- ranking evidence, ambiguity markers, selected plate-object specs, and execution-contract semantics are persisted in sidecar metadata.
- logs also surface runtime env snapshot, ranked candidate summaries, and placement semantics.

## Phase G: Test expansion

Add or redesign tests for:

- multiple `EXCLUDE_OBJECT_DEFINE` objects in one file
- `M486`-derived object grouping
- per-object bounds inference across layers
- `G90` and `G91` and `G92` effects during inference
- moved and rotated object alignment
- duplicated objects and arranged plates
- transform round-trip into sidecar metadata
- Stage 2 pivot correctness during rotation plus translation

## Explicit exclusions from the first implementation phase

- full automatic rotation inference from toolpath geometry alone
- arbitrary STL-to-toolpath registration without metadata
- multi-mesh scene solving for overlapping unknown objects

## Research-backed rationale

- Klipper's documented contract supports a richer object model than JAA currently uses.
- OrcaSlicer inconsistency means normalization is not optional.
- Center-only metadata is insufficient for crowded or overlapping plates; polygons exist precisely to address that case.
- Existing non-planar and conformal toolpath work reinforces the value of region-aware processing and explicit geometry provenance.

## Deliverables expected from this plan

- canonical object metadata schema
- normalization strategy for multiple slicer dialects
- per-object transform inference design
- deterministic mesh placement semantics
- expanded regression surface for transform correctness