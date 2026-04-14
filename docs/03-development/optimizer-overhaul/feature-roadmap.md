# Optional Feature Roadmap

This document separates optional and research-backed feature ideas from the must-do correctness and performance foundation.

## Roadmap philosophy

- Only promote a feature into the active implementation queue if it has a clear value proposition, a validation path, and does not undermine the core transform and safety work.
- Group features by maturity: near-term, medium-term, long-term research.

## Near-term optional features

1. Richer transform diagnostics
   - per-object transform summaries in sidecar metadata
   - ambiguity and fallback reasons
   - optional debug output for object windows and inferred bounds
   - value: immediate supportability and lower debugging cost

2. Visual debug artifacts
   - object window overlays
   - inferred bounds and polygon previews
   - optional Stage 2 point-sampling evidence
   - research basis: practical non-planar tools such as NonPlanarIroning emphasize debug visualization and reachability logs

3. Benchmark evidence packs
   - save repeatable benchmark outputs for known fixtures
   - enable before and after comparison on throughput work
   - value: prevents ungrounded optimization claims

4. Smarter Stage 2 policy controls
   - more explicit skip and force behavior for GPU requirements, transform ambiguity, or missing metadata
   - value: safer operator experience

## Medium-term optional features

1. Per-object Stage 2 processing on arranged plates
   - process multiple objects with independent transforms and metadata
   - requires the transform redesign to land first

2. Polygon-aware object inference
   - use `POLYGON` if present for better centroids and ambiguity handling
   - useful when objects are close together or overlapping in XY bounds

3. Segmented non-planar processing
   - break complex regions into smaller analyzable sections or bands
   - research basis: non-planar repos and papers repeatedly use segmented region logic and collision scopes

4. Selective deformation utilities
   - allow targeted Z deformation or region-specific behavior rather than only full-object behavior
   - research basis: conformal and post-process tooling emphasizes selective Z raises and filtered line transformations

5. Better operator-facing research output
   - provide machine-readable evidence about whether a file is a good candidate for non-planar processing, aggressive sampling, or Stage 3 compression

## Long-term research features

1. Hybrid Open3D query pipeline
   - combine raycasts with distance, occlusion, or closest-point queries where benchmark data justifies it
   - prerequisite: stable correctness and benchmark harness

2. Mesh or toolpath reconciliation
   - compare STL-derived geometry with motion-derived bounds or polygons to detect likely placement mismatch
   - possible outputs: warning only, confidence downgrade, or guided suggestion

3. Heuristic rotation inference
   - use polygon orientation, PCA, or path-direction heuristics to infer missing rotation
   - high risk of false confidence; only consider behind explicit confidence scoring and operator override

4. Multi-model or cached scene management
   - reuse or pool scene data across multiple files or repeated runs
   - requires memory-lifetime and device-behavior validation

5. Firmware-aware Stage 3 decisions
   - adapt arc compression policy to known firmware capabilities and caveats
   - research basis: Arc Welder notes uneven firmware behavior and interpolation differences

## Deferred or intentionally low-priority ideas

- replacing Open3D as the Stage 2 engine
- building a slicer plugin as the main integration path
- fully automatic support-aware collision planning
- end-user GUI design for transform calibration during the first optimization wave

## Promotion criteria for any optional feature

A feature can move from roadmap to active implementation only if:

1. there is evidence that it solves a real problem seen in this repository or its target slicer ecosystem
2. the required metadata and invariants are understood
3. there is a practical regression or benchmark plan
4. the feature does not rely on silently guessing ambiguous geometry

## Suggested sequencing

- First promote diagnostics and benchmark evidence.
- Next promote polygon-aware and per-object transform work.
- Only then consider segmented processing, selective deformation, or hybrid query strategies.

## Research-backed rationale

- Klipper object metadata and OrcaSlicer issues justify polygon-aware and normalization features.
- Non-planar literature justifies segmented collision-aware processing and geometry suitability analysis.
- Arc Welder documentation justifies firmware-aware Stage 3 policy rather than treating arc compression as universally beneficial.
- Open3D documentation justifies exploring hybrid query strategies only after the current batched scene model is benchmarked thoroughly.