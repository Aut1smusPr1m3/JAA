# Validation and Rollout Plan

This document defines how the roadmap should be validated and phased so high-risk changes do not land on intuition alone.

## Principle

Every major change in this roadmap must prove three things:

- it preserves safety invariants
- it improves correctness or makes ambiguity visible
- it is measurably worthwhile when the change is about performance or optional features

## Phase 0: Fixture design

Build a stable validation corpus that includes:

1. simple single-object G-code with stable transform
2. moved object with explicit hint metadata
3. rotated object with explicit metadata
4. file with only bounds-based inference
5. multi-object arranged plate with distinguishable objects
6. object metadata in Klipper form with `CENTER` and `POLYGON`
7. metadata-poor or `M486`-like object markers requiring normalization
8. no-STL Stage 2 skip path
9. ArcWelder-enabled and ArcWelder-disabled variants
10. long-segment and pathological sampling stress cases

## Phase 1: Correctness gates

The following must pass before optimization phases merge:

- `python -m pytest -q`
- transform provenance tests
- per-object window extraction tests
- `G90` and `G91` and `G92` inference tests
- mesh rotation and translation pivot tests
- arranged-plate object-switching and analyzer-reset tests
- sidecar execution-contract validation tests
- sidecar round-trip tests
- no-final-negative-Z checks

## Phase 2: Benchmark gates

Use the repository benchmark hooks and define a result format that captures:

- elapsed time per stage
- raycast scene build time
- number of qualifying moves
- number of skipped moves with reasons
- rays cast and batch counts
- sample caps hit
- selected device and fallback cause
- Stage 3 compression evidence

Do not accept a result that is only faster on one run as proof. Require repeated runs on the same corpus and compare medians or stable representative values.

## Phase 3: Manual validation gates

Manual end-to-end inspection should cover:

- moved and rotated single-object alignment
- crowded arranged-plate alignment
- arranged-plate scene switching where multiple objects share the same STL but differ in position or rotation
- transform ambiguity warnings when metadata is incomplete
- Stage 2 fallback when STL or GPU support is unavailable
- Stage 3 output on known firmware-compatible workflows

## Phase 4: Rollout order

1. land observability and benchmark harness improvements
2. land canonical metadata schema and normalization scaffolding
3. land per-object transform redesign with tests
4. land Stage 2 mesh-placement semantics
5. land the backward-compatible multi-object dispatch contract and arranged-plate execution regressions
6. land sidecar execution evidence and rollout documentation
7. land low-risk throughput work
8. land optional feature increments only after the previous phases are stable

## Rollback criteria

A change should be rolled back or paused if it introduces any of the following:

- silent transform ambiguity or hidden fallback behavior
- new negative-Z or safety violations
- degraded handling of no-STL or no-GPU fallback paths
- arranged-plate object switches reusing the wrong scene or leaking analyzer state between objects
- benchmark regressions without a corresponding correctness win
- multi-object files collapsing incorrectly to one inferred transform

## Evidence artifacts to preserve

- benchmark logs
- sidecar metadata samples before and after redesign
- representative transformed G-code outputs
- manual validation notes tied to fixture names
- perf evidence from the existing benchmark scripts

## Research-backed rationale

- Literature on non-planar path generation repeatedly shows that correctness, collision handling, and geometry suitability must be established before chasing speed.
- Open3D's documented API surface supports experimentation, but only a benchmarked harness can show whether an alternative query mode helps this codebase.
- Slicer metadata inconsistency in the ecosystem means validation must include malformed or partially normalized real-world cases.

## Deliverables expected from this plan

- fixture matrix
- test expansion matrix
- benchmark acceptance criteria
- rollout sequence that protects correctness-first changes from being buried under speculative optimization
- explicit validation gates for pivot semantics, arranged-plate execution switching, and sidecar execution-contract evidence