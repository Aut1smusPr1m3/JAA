# Changelog

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
