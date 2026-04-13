# Installation

## Requirements
- Python 3.11 or 3.12
- Core dependency: `numpy`
- Optional Stage 2 full raycasting dependency: `open3d`
- Dev dependencies (tests/lint): `pytest`, `ruff`, `pre-commit`

## Requirements files
- `requirements.txt`: core runtime dependencies.
- `requirements-optional.txt`: optional dependencies for full Stage 2 workflows.
- `requirements-windows.txt`: combined core + optional set for Windows AIO installs.
- `requirements-dev.txt`: developer tooling and test dependencies.

## Install
Create and activate a virtual environment first:
```bash
python -m venv .venv
source .venv/bin/activate
```

Then install dependencies:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For development:
```bash
pip install -r requirements-dev.txt
```

For full Stage 2 raycasting support:
```bash
pip install -r requirements-optional.txt
```

## Windows AIO bootstrap
From PowerShell in repository root:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev
```

Or with Batch launcher:
```bat
scripts\windows\bootstrap.bat -InstallDev
```

If `ArcWelder.exe` is missing in repo root, provide one source:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -ArcWelderPath "C:\path\to\ArcWelder.exe"
```
or
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -ArcWelderUrl "https://example.com/ArcWelder.exe"
```

## Optional advanced dependency
Open3D is optional, but required for full Stage 2 STL raycasting quality workflows.

If Open3D is missing:
- core processing still works,
- Stage 2 raycasting is skipped/fallback behavior is used.

## Critical warning
- Always run `Ultra_Optimizer.py` from this same activated virtual environment. If OrcaSlicer invokes a different Python interpreter, behavior can differ from terminal tests.

## Next steps
- [Windows AIO setup](windows-aio-setup.md)
- [OrcaSlicer integration](orcaslicer-integration.md)
- [Troubleshooting](troubleshooting.md)
- [Pipeline stages reference](../02-technical-reference/pipeline-stages.md)
