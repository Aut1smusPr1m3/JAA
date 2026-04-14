# Research Synthesis

This document summarizes the external research that informed the optimizer overhaul plan. It is intentionally scoped to decisions that affect JAA's near-term roadmap.

## Scope

The synthesis covers three workstreams:

- whole-pipeline optimization and observability
- automatic STL/object translation and rotation inference
- optional new features grounded in current practice, existing implementations, and literature

## Internal baseline from repository analysis

- The repository is a three-stage pipeline: Stage 1 in `Ultra_Optimizer.py`, Stage 2 in `GCodeZAA/gcodezaa/process.py`, and Stage 3 in `Ultra_Optimizer.py` via ArcWelder.
- The main correctness weakness is transform resolution: `resolve_stage2_object_transform()` is effectively single-object and relies on hints, `EXCLUDE_OBJECT_DEFINE`, or printable-window bounds.
- The main throughput hotspot is the Stage 2 raycast/sampling path in `GCodeZAA/gcodezaa/surface_analysis.py`.

## Theme 1: Raycasting and Stage 2 performance

### Sources reviewed

- Open3D RaycastingScene docs: https://www.open3d.org/docs/latest/python_api/open3d.t.geometry.RaycastingScene.html
- Context7 Open3D docs for `/isl-org/open3d`

### Findings

- Open3D documents `cast_rays`, `compute_closest_points`, `compute_distance`, `compute_signed_distance`, `compute_occupancy`, `count_intersections`, `list_intersections`, and `test_occlusions` as supported query primitives.
- Open3D explicitly supports CPU and SYCL devices for `RaycastingScene`; SYCL support is documented as tested primarily on Linux and a single GPU.
- Query APIs accept tensor-shaped batched inputs. This validates the repository's batch-first design and supports further batch-centric optimization.
- The presence of non-ray query methods creates a realistic research track for selective optimization. Some move classes may be rejectable through occupancy, occlusion, or distance checks before full bidirectional raycasts.

### Implications for JAA

- Keep the near-term focus on improving the current batched raycast approach rather than replacing it.
- Add a research track for hybrid query strategies only after current semantics are stabilized.
- Treat device-aware batch sizing, scene reuse, and lower Python overhead as high-confidence optimization areas.

## Theme 2: Object metadata, transform inference, and slicer reality

### Sources reviewed

- Klipper Exclude Object docs: https://www.klipper3d.org/Exclude_Object.html
- GitHub mirror of the Klipper docs: https://github.com/Klipper3d/klipper/blob/master/docs/Exclude_Object.md
- OrcaSlicer issue on wrong Klipper object output: https://github.com/OrcaSlicer/OrcaSlicer/issues/13101

### Findings

- Klipper's intended object metadata contract includes `EXCLUDE_OBJECT_DEFINE`, `EXCLUDE_OBJECT_START`, `EXCLUDE_OBJECT_END`, `CENTER`, and `POLYGON`.
- Klipper's documentation is explicit that preprocessing is expected before printing; object metadata is not guaranteed to come directly from the slicer in the desired form.
- `POLYGON` exists specifically because center-only metadata becomes inadequate when multiple objects overlap or are visually close.
- OrcaSlicer currently has real-world cases where Klipper-flavored output still emits Marlin-style `M486` markers and omits `DEFINE CENTER/POLYGON`, meaning downstream normalization is a real-world need, not a hypothetical edge case.
- Community requests around OrcaSlicer-to-Klipper conversion explicitly describe computing centers and polygons from object blocks and mapping marker semantics carefully.

### Implications for JAA

- The transform redesign should not assume consistent upstream slicer metadata.
- The plan must include a normalization layer capable of parsing multiple metadata families: JAA hints, Klipper-style markers, Marlin-style M486 flows, and fallback motion-derived windows.
- Per-object polygons and boundaries should be treated as first-class data for future multi-object transform resolution.
- Automatic inference should degrade visibly with provenance and warnings, not silently collapse to a single global window.

## Theme 3: Non-planar and conformal printing literature

### Sources reviewed

- Ahlers et al., "3D Printing of Nonplanar Layers for Smooth Surface Generation": https://tams.informatik.uni-hamburg.de/publications/2019/case_ahlers_2019.pdf
- 2025 Results in Engineering paper on CLFDM: https://www.sciencedirect.com/science/article/pii/S2590123025043178
- Conformal 3D Printing repo: https://github.com/cam-cambridge/Conformal-3D-Printing
- NonPlanarIroning repo: https://github.com/TengerTechnologies/NonPlanarIroning

### Findings

- Non-planar printing literature consistently emphasizes three issues: region classification, collision avoidance, and dynamic extrusion compensation.
- Ahlers et al. describe automatic surface suitability detection, collision envelopes, projection of 2D paths onto 3D surfaces, insertion of additional points at facet intersections, and slope-aware extrusion compensation.
- Their reported bottleneck is also geometric intersection cost; they explicitly call out the need for better spatial queries and parallelization.
- The 2025 CLFDM paper reports improved surface finish on suitable geometries, but also reinforces that feasibility is geometry-dependent and collision-free path generation is central.
- Existing practical repos such as NonPlanarIroning emphasize debug tooling, visualization, segmentation/banding, and collision-scope control rather than only core path deformation.
- Conformal/post-process repos also show value in a reusable parsed G-code model with bbox, line filtering, and selective Z deformation utilities.

### Implications for JAA

- Stage 2 work should continue to prioritize surface suitability detection and collision-aware behavior.
- Optional feature planning should include visualization, debug evidence, segmented processing, and selective deformation tools as realistic future additions.
- Performance work should explicitly consider spatial indexing, smarter sampling, and batched geometry intersections as literature-backed directions.

## Theme 4: Arc compression and Stage 3 policy

### Sources reviewed

- Arc Welder overview and implementation notes: https://plugins.octoprint.org/plugins/arc_welder/

### Findings

- Arc Welder's value proposition is strongest on dense sequences of short moves; 3DBenchy examples still show large file-size and move-count reductions.
- Arc fitting is constrained by printer state changes such as feedrate or offset changes and by deviation thresholds.
- Firmware support is uneven. Klipper works with `gcode_arcs`; Marlin and Prusa variants have caveats and interpolation differences.
- Arc Welder's core parser is implemented in C++, highlighting a gap between JAA's Python orchestration and performance-critical parsing/compression tasks.

### Implications for JAA

- Stage 3 planning should remain optional and firmware-aware.
- Better Stage 3 diagnostics and policy gates are higher value than large Stage 3 rewrites.
- If deeper Stage 3 optimization is pursued later, consider whether some pre-filtering or analytics should happen before invoking the external tool, not inside Python-heavy loops.

## Cross-cutting conclusions

1. The repository's next major milestone should be transform correctness and metadata normalization, not raw speed alone.
2. Full slicer-layout awareness is justified by both Klipper's intended model and OrcaSlicer's inconsistent real-world output.
3. Stage 2 performance improvements should be benchmark-driven and mostly evolutionary at first: smarter gating, better batching, better sampling, and more structured provenance.
4. Optional feature work should stay aligned with the literature: collision-aware non-planar processing, region classification, segmented workflows, visual diagnostics, and geometry-aware compensation.
5. The plan should distinguish high-confidence deliverables from speculative research. Open3D hybrid queries, mesh/toolpath registration, and advanced per-object reconciliation belong in a later research-backed phase, not the first implementation phase.

## Recommended planning posture

- Foundation first: normalize object metadata and make transform provenance explicit.
- Then correctness: make mesh transform application deterministic and testable.
- Then speed: optimize Stage 2 and only then tune Stage 1 and Stage 3.
- Then features: add richer multi-object and non-planar capabilities behind strong validation.