# Windows AIO Release

This repository includes automated Windows AIO release packaging via:
- `.github/workflows/windows-aio-release.yml`

## What the workflow does
1. Runs on tag pushes matching `v*` and on manual dispatch.
2. Installs dev + optional dependencies.
3. Runs full test suite.
4. Builds a Windows AIO zip bundle.
5. Builds standalone wheelhouse zip assets:
	- Windows CPython 3.12 wheelhouse,
	- Linux CPython 3.12 wheelhouse.
6. Uploads all zip files as workflow artifacts.
7. Publishes all zip files as GitHub Release assets when the run is tag-triggered.

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

## Additional release assets
- `Ultra_Optimizer-Wheelhouse-windows-py312-<version>.zip`
- `Ultra_Optimizer-Wheelhouse-linux-py312-<version>.zip`

Each wheelhouse zip includes `SHA256SUMS.txt` for integrity verification.

## Local preflight before tagging
```bash
python -m pytest -q -r s
```

## License compliance gate
Before publishing tag-triggered release assets:
1. Run the checklist in [License compliance checklist](license-compliance.md).
2. Refresh dependency evidence from [Dependency license inventory](../04-reference/dependency-licenses.md).
3. Ensure release artifacts include project `LICENSE` and dependency notice references.
