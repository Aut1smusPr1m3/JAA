# Changelog

## v0.2.1-alpha.4 - GPU acceleration groundwork (SYCL device routing)

### Added
- Stage 2 raycast device selection controls:
  - `GCODEZAA_RAYCAST_DEVICE=auto|cpu:0|sycl:0`
  - `GCODEZAA_REQUIRE_GPU=1` to fail fast when GPU is required but unavailable
- Device-selection tests:
  - `test_gcodezaa_device_selection.py`

### Changed
- STL loading and raycasting scene creation now route through resolved Open3D device target.
- Surface analyzer now builds ray tensors on the selected device.
- EXCLUDE_OBJECT stage flow now tracks object-associated raycast devices.

### Validation
- `python -m pytest -q`
- Result: `55 passed, 3 skipped`
- Repeatable benchy runs with device modes:
  - `GCODEZAA_RAYCAST_DEVICE=auto`
  - `GCODEZAA_RAYCAST_DEVICE=sycl:0`
  - both completed safely with `negative_z_commands=0`

## v0.2.1-alpha.2 - High-throughput Stage 2 raycasting

### Added
- Throughput regression tests:
  - `test_gcodezaa_throughput.py`
- Optional built-in pipeline profiling:
  - `ULTRA_OPTIMIZER_PROFILE=1`
  - output file: `ultra_optimizer_profile.prof`

### Changed
- Stage 2 only raycasts qualifying surface-following extrusion moves (skips travel/non-extrusion moves).
- Arc decomposition/raycasting is now skipped when surface-following is not applicable.
- Ray submission now batches upward/downward casts in one vectorized Open3D tensor call.
- Segment sampling is bounded by `GCODEZAA_MAX_SEGMENT_SAMPLES` to prevent runaway point counts.
- New tunables for throughput:
  - `GCODEZAA_SAMPLE_DISTANCE_MM`
  - `GCODEZAA_MAX_SEGMENT_SAMPLES`
  - `GCODEZAA_BATCH_RAY_SIZE`

### Validation
- `python -m pytest -q`
- Result: `50 passed, 3 skipped`
- Sample-count reduction check (200mm segment): `4001 -> 192` points (~20.84x fewer samples)

## v0.2.1-alpha.1 - Safety hardening for alpha testing

### Added
- Hard negative-Z safety enforcement in final pipeline output:
  - clamp all `G0/G1/G2/G3/G92` Z commands to `Z>=0.0`
  - fail pipeline if any negative-Z command remains after sanitation
- New safety regression tests:
  - `test_safety_guards.py`

### Changed
- Stage 2 contour generation now clamps build-surface-following moves to the build plate floor.
- Smoothing-angle handling now uses a hard cap of `45deg` in both integration and surface-analysis layers.

### Validation
- `python -m pytest -q`
- Result: `46 passed, 3 skipped`
- End-to-end smoke run via `python Ultra_Optimizer.py /tmp/jaa_safety_smoke.gcode`
- Verified post-run negative-Z scan result: `0`

## v0.2.0 - Windows AIO bootstrap and release automation

### Added
- Windows bootstrap installer scripts:
  - `scripts/windows/bootstrap.ps1`
  - `scripts/windows/bootstrap.bat`
- Windows release workflow:
  - `.github/workflows/windows-aio-release.yml`
- Requirements split for runtime/dev/optional/full-Windows installs:
  - `requirements.txt`
  - `requirements-dev.txt`
  - `requirements-optional.txt`
  - `requirements-windows.txt`
- Windows AIO docs:
  - `docs/01-user-guides/windows-aio-setup.md`
  - `docs/03-development/release-aio.md`

### Changed
- `README.md` and installation docs now document AIO bootstrap setup.
- `.gitignore` now excludes `.venv/` created by bootstrap.

### Validation
- `python -m pytest -q -r s`
- Result: `41 passed, 3 skipped`
