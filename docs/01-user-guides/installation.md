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

Offline install from release wheelhouse:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -UseBundledWheels
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

Windows custom SYCL toolchain/setup path (no NVIDIA driver modifications):
```powershell
./scripts/windows/bootstrap.ps1 -SetupSyclToolchain -InstallOneApiBaseToolkit
./scripts/windows/bootstrap.ps1 -SetupSyclToolchain -BuildOpen3DSyclWithWsl -WslDistro Ubuntu
```

## Optional advanced dependency
Open3D is optional, but required for full Stage 2 STL raycasting quality workflows.

If Open3D is missing:
- core processing still works,
- Stage 2 raycasting is skipped/fallback behavior is used.

## Linux SYCL GPU installation path (Open3D upstream guidance)
Open3D's prebuilt SYCL Python wheels are Linux-focused (Ubuntu 22.04+).

Use the helper script to install an `open3d_xpu` wheel and verify SYCL device visibility:

```bash
bash scripts/linux/install_open3d_sycl.sh
```

What this script does:
- installs a Linux x86_64 `open3d_xpu` wheel for your Python version,
- verifies `open3d.core.sycl` is available,
- checks SYCL devices and `SYCL:0` availability,
- warns if no GPU-capable SYCL device is detected.

Environment overrides:
- `OPEN3D_SYCL_VERSION` to change expected wheel version,
- `OPEN3D_SYCL_BASE_URL` to change release base URL,
- `OPEN3D_SYCL_WHEEL_URL` to provide an explicit wheel URL.

Notes from upstream guidance:
- install correct GPU drivers/runtime,
- for Intel GPU raycasting, install `intel-level-zero-gpu-raytracing`.

## Critical warning
- Always run `Ultra_Optimizer.py` from this same activated virtual environment. If OrcaSlicer invokes a different Python interpreter, behavior can differ from terminal tests.

## Next steps
- [Windows AIO setup](windows-aio-setup.md)
- [OrcaSlicer integration](orcaslicer-integration.md)
- [Troubleshooting](troubleshooting.md)
- [Pipeline stages reference](../02-technical-reference/pipeline-stages.md)
