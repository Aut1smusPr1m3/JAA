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
git tag v2.2
git push origin v2.2
```

Alpha prerelease flow (example):
```bash
git tag v2.2-rc.1
git push origin v2.2-rc.1
```

If you create the GitHub release manually, mark it as a prerelease.

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

## License compliance gate
Before publishing tag-triggered release assets:
1. Run the checklist in [License compliance checklist](license-compliance.md).
2. Refresh dependency evidence from [Dependency license inventory](../04-reference/dependency-licenses.md).
3. Ensure release artifacts include project `LICENSE` and dependency notice references.
