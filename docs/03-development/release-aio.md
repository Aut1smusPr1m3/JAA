# Windows AIO Release

This repository includes automated Windows AIO release packaging via:
- `.github/workflows/windows-aio-release.yml`

## What the workflow does
1. Runs on tag pushes matching `v*` and on manual dispatch.
2. Installs dev + optional dependencies.
3. Runs full test suite.
4. Builds a Windows AIO zip bundle.
5. Uploads the bundle as a workflow artifact.
6. Publishes a GitHub Release asset when the run is tag-triggered.

## Tag-based release flow
```bash
git tag v0.1.0
git push origin v0.1.0
```

## Bundle contents
- `Ultra_Optimizer.py`
- `ArcWelder.exe` (when present in repository)
- `requirements*.txt`
- `docs/`
- `GCodeZAA/`
- `scripts/windows/`
- `INSTALL_WINDOWS_AIO.bat`

## Local preflight before tagging
```bash
python -m pytest -q -r s
```
