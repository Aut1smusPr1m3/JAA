# Changelog

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
