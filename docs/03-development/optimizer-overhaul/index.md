# Optimizer Overhaul Planning Pack

This planning pack turns the repository analysis and external research pass into an execution-oriented set of documents for the next major development cycle.

The pack is organized so that correctness and observability work lands before aggressive optimization, and so optional features stay separated from the first implementation wave.

## Recommended posture

- Stabilize semantics before optimizing aggressively.
- Redesign transform handling around a canonical object model that can normalize real-world slicer metadata.
- Optimize Stage 2 first, because it is the main performance hotspot, but only after transform correctness is reliable.
- Keep optional features in a separate roadmap so foundation work is not diluted by speculative research.

## Document map

1. [Research Synthesis](./research-synthesis.md)
   External research across Open3D, Klipper object metadata, OrcaSlicer ecosystem issues, non-planar printing literature, conformal/non-planar implementations, and Arc Welder.

2. [Pipeline Optimization Plan](./pipeline-optimization.md)
   Detailed whole-pipeline optimization plan for Stages 1, 2, and 3, including evidence requirements, metrics, and sequencing.

3. [Transform Redesign Plan](./transform-redesign.md)
   Detailed redesign of object translation and rotation handling, including canonical metadata, normalization, per-object windows, inference strategy, and mesh-placement semantics.

4. [Transform Implementation Spec](./implementation-spec.md)
   Function-level implementation notes for the first transform and observability milestones, including proposed data structures and concrete code touch points.

5. [Validation Fixture and Test Matrix](./fixture-test-matrix.md)
   Fixture design and test mapping tied directly to the current pytest files.

6. [Optional Feature Roadmap](./feature-roadmap.md)
   Optional feature roadmap grouped into near-term, medium-term, and long-term research tracks.

7. [Validation and Rollout Plan](./validation-rollout.md)
   Test, benchmark, manual-validation, and rollout gating plan.

## Recommended execution order

1. Validation groundwork
   Use [Validation and Rollout Plan](./validation-rollout.md) to define fixtures and acceptance criteria first.

2. Transform foundation
   Execute [Transform Redesign Plan](./transform-redesign.md) before major Stage 2 optimization.

3. Pipeline optimization
   Execute [Pipeline Optimization Plan](./pipeline-optimization.md) after transform semantics are stable enough to benchmark meaningfully.

4. Optional feature promotion
   Draw from [Optional Feature Roadmap](./feature-roadmap.md) only after the previous three tracks are stable.

## Core decisions carried forward

- Balanced roadmap: pipeline optimization and transform redesign are both first-class goals.
- Full slicer-layout awareness: the redesign should not stop at single-object reliability.
- Ambitious roadmap: include larger future-facing ideas, but separate them from the initial foundation.

## Scope boundaries

Included:

- Stage 1, Stage 2, Stage 3, metadata, benchmarks, transform inference, per-object handling, and research-backed feature planning.

Excluded from the first implementation wave:

- replacing Open3D
- firmware modifications
- new slicer plugin development

## Milestone framing

1. Milestone 1: validation harness plus transform schema
2. Milestone 2: object normalization and per-object windows
3. Milestone 3: mesh placement correctness
4. Milestone 4: Stage 2 throughput optimization
5. Milestone 5: optional feature promotions

## Key research conclusions shaping the pack

- Klipper's object model and OrcaSlicer's inconsistent output justify a normalization layer and per-object metadata model.
- Open3D's documented query surface supports batched optimization now and hybrid-query research later.
- Non-planar printing literature strongly supports a correctness-first approach centered on collision-aware geometry handling, region classification, and explicit compensation.
- Arc compression remains valuable but should stay policy-driven and optional.