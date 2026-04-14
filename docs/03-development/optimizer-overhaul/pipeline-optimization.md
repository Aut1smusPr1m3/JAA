# Pipeline Optimization Plan

This document covers the execution plan for optimizing and hardening the complete JAA pipeline across Stages 1, 2, and 3.

## Objectives

- improve throughput without weakening safety guarantees
- make performance measurable with stable evidence
- remove avoidable overhead before considering higher-risk algorithm changes
- preserve Stage 1 always-run behavior and optional Stage 2/3 fallbacks

## Baseline assumptions from repository state

- Stage 1 is window-aware kinematic shaping in `Ultra_Optimizer.py`.
- Stage 2 is the main performance hotspot in `GCodeZAA/gcodezaa/process.py` and `GCodeZAA/gcodezaa/surface_analysis.py`.
- Stage 3 is optional external arc compression.
- Existing benchmark hooks already exist in `scripts/perf/profile_benchy.sh` and `scripts/perf/capture_stage2_evidence.sh`.

## Phase A: Baseline, observability, and fixture quality

1. Define a fixed benchmark corpus:
   - single-object standard print
   - moved and rotated object
   - multi-object arranged plate
   - long-segment stress file
   - no-STL fallback file
   - ArcWelder-enabled file

2. Extend evidence capture so each run records:
   - Stage 1 elapsed time
   - Stage 2 scene build time
   - Stage 2 processed qualifying moves count
   - raycast batch count and average batch size
   - sample count distribution
   - skip reasons for moves and segments
   - device selection and fallback reason
   - Stage 3 invocation result, file delta, and output hash state

3. Treat this phase as mandatory before any optimization change merges.

## Phase B: Stage 2 low-risk throughput wins

1. Optimize pre-raycast gating in `process_line()` so non-qualifying moves are rejected earlier with cheaper checks.
2. Refine adaptive sampling in `SurfaceAnalyzer._adaptive_sample_distance()` to distinguish:
   - very short segments
   - ordinary perimeter segments
   - long traversal-like extrusion segments
3. Add stronger sample-capping telemetry so the system can show when runtime is being driven by over-sampling rather than scene build.
4. Investigate device-aware `BATCH_RAY_SIZE` tuning so small-memory GPUs or fallback CPU paths do not use the same static batch strategy.
5. Reduce Python overhead in per-line Stage 2 processing where repeated parsing or repeated state lookups are avoidable.

## Phase C: Stage 2 structural optimization after correctness stabilizes

1. Evaluate scene reuse or caching for repeated runs against the same STL or fixture set.
2. Evaluate whether raycast preparation can reuse preallocated tensor buffers or reduce temporary allocations.
3. Test hybrid query strategies only as an opt-in branch:
   - `test_occlusions()` for early reject checks
   - `compute_distance()` or `compute_closest_points()` for select move classes
   - signed-distance or occupancy queries only if watertightness assumptions are safe
4. Reject speculative optimization paths unless they beat the baseline with no behavior regression.

## Phase D: Stage 1 optimization

1. Audit repeated regex parsing and motion extraction in `safe_parse_g1()`, `safe_parse_arc()`, and the main Stage 1 loop.
2. Reduce redundant work across:
   - window detection
   - state priming
   - feedrate priming
   - sidecar-related passes that can be merged or deferred
3. Preserve start and end G-code invariants and acceleration injection semantics.
4. Treat Stage 1 refactors as low-risk only if they do not alter window precedence or `M204` behavior.

## Phase E: Stage 3 policy and diagnostics

1. Keep ArcWelder external and optional.
2. Improve Stage 3 evidence collection:
   - pre and post size metrics
   - move count deltas where available
   - firmware-compatibility warnings
   - whether comments or metadata continuity is affected
3. Add configuration policy for when Stage 3 should be skipped automatically, for example based on firmware profile or file characteristics, if later evidence justifies it.

## Metrics that matter

- wall-clock runtime per stage
- Stage 2 qualifying-move rate vs total moves
- average and capped samples per segment
- number of raycast batches and total rays cast
- scene build time vs process time split
- file size and move-count reduction after Stage 3
- regression counts in transform correctness and safety tests

## Verification

1. `python -m pytest -q`
2. Repeat benchmark runs with the same fixture set before and after each optimization phase.
3. Compare logs and sidecar evidence, not just elapsed time.
4. Require no regressions in negative-Z enforcement, window detection, transform provenance, or optional-stage fallback behavior.

## Research-backed rationale

- Open3D documents batched tensor-based queries and CPU/SYCL support, which supports continued batch-first optimization.
- Non-planar literature repeatedly identifies spatial queries and projection cost as bottlenecks, which aligns with current Stage 2 hotspots.
- Arc Welder's value is tied to dense short segments and external high-performance parsing, which argues for better policy and diagnostics rather than a full rewrite.

## Deliverables expected from this plan

- a benchmark corpus and evidence format
- prioritized optimization backlog with measured wins
- safer Stage 2 throughput improvements before deeper algorithm changes
- a clearer basis for deciding whether advanced research tracks are worth implementing