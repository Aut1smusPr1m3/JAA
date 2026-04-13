# Windows AIO Setup

This guide installs a complete Windows-ready environment for Ultra_Optimizer:
- virtual environment,
- Python packages,
- optional Open3D,
- ArcWelder executable provisioning,
- optional test run.

## Quick start
From repository root in PowerShell:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev
```

Equivalent Batch launcher:
```bat
scripts\windows\bootstrap.bat -InstallDev
```

Optional lightweight GUI launcher (Windows only):
```powershell
python scripts/windows/bootstrap_gui.py
```

## Default behavior
- Creates or reuses `.venv`.
- Installs `requirements.txt`.
- Installs `requirements-optional.txt` by default.
- Installs `requirements-dev.txt` when `-InstallDev` is provided.
- Ensures `ArcWelder.exe` exists in repo root.
- Creates `stl_models/` if missing.
- Release bundles now include a `wheels/` wheelhouse for offline installs.

## ArcWelder provisioning
If `ArcWelder.exe` is already in repo root, nothing else is required.

If it is missing, provide one source:
```powershell
./scripts/windows/bootstrap.ps1 -ArcWelderPath "C:\path\to\ArcWelder.exe"
```

or
```powershell
./scripts/windows/bootstrap.ps1 -ArcWelderUrl "https://example.com/ArcWelder.exe"
```

## Useful options
- Skip Open3D install:
```powershell
./scripts/windows/bootstrap.ps1 -InstallOpen3D:$false
```

- Install from bundled wheelhouse (release zip):
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -UseBundledWheels
```

- Custom wheelhouse location:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -UseBundledWheels -WheelhousePath "wheels"
```

- Install Open3D from an explicit custom wheel:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -Open3DWheelPath "wheels\open3d_custom.whl"
```

- Require SYCL GPU (fail install if unavailable):
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -RequireSyclGpu
```

Important:
- Open3D upstream prebuilt SYCL Python wheels target Linux (Ubuntu 22.04+) workflows.
- On Windows, strict SYCL GPU mode usually requires a custom Open3D/SYCL toolchain build and proper GPU runtime/drivers.
- This bootstrap does not install or modify NVIDIA GPU drivers.

- Setup SYCL toolchain checks on Windows (oneAPI + sycl-ls probe):
```powershell
./scripts/windows/bootstrap.ps1 -SetupSyclToolchain
```

- Optionally install Intel oneAPI Base Toolkit via winget during setup:
```powershell
./scripts/windows/bootstrap.ps1 -SetupSyclToolchain -InstallOneApiBaseToolkit
```

- Build Open3D SYCL from source in WSL (custom build path):
```powershell
./scripts/windows/bootstrap.ps1 -SetupSyclToolchain -BuildOpen3DSyclWithWsl -WslDistro Ubuntu
```

- Skip tests:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -SkipTests
```

- Custom venv path:
```powershell
./scripts/windows/bootstrap.ps1 -VenvPath ".venv-win"
```

## GUI installer notes
- The GUI wraps `scripts/windows/bootstrap.ps1` and streams live output.
- Configure the same options as CLI mode (dev deps, Open3D, tests, venv path, ArcWelder path/URL).
- Optional strict mode is available to require SYCL GPU support during install.
- Provide either ArcWelder path OR ArcWelder URL, not both.

## Expected output markers
During a successful run, expect these checkpoints in PowerShell output:
- `[INFO] Repo root: ...`
- `[INFO] Python launcher: ...`
- `[INFO] Installing dependencies`
- `[INFO] Running bootstrap smoke checks`
- `numpy <version>` and `open3d True/False`
- `[INFO] Running Open3D SYCL capability check`
- `[INFO] SYCL devices: ...`
- `[INFO] SYCL:0 available: True/False`
- `[INFO] SYCL GPU candidates: ...`
- `[INFO] Installing from bundled wheelhouse: ...` (when enabled)
- `[INFO] Starting Windows SYCL toolchain setup` (when enabled)
- `[SUCCESS] Windows bootstrap completed.`

## Common failure signatures
- `No compatible Python launcher found. Install Python 3.11 or 3.12 first.`
: Install supported Python and re-run from a new shell.
- `ArcWelder.exe not found. Provide -ArcWelderPath or -ArcWelderUrl.`
: Provide one ArcWelder source argument.
- `ArcWelderPath does not exist: ...`
: Verify file path and permissions.
- `Virtual environment python not found: ...`
: Remove broken venv path and re-run bootstrap.
- `SYCL GPU check failed. Use Open3D SYCL setup guidance (Linux x86_64 wheel/runtime or custom build), install correct GPU drivers, and ensure at least one SYCL GPU device is available.`
: Follow Linux SYCL install guidance in [installation.md](installation.md), or run without `-RequireSyclGpu`.
- `Bundled wheelhouse not found: ...`
: Ensure the release zip includes `wheels/` and run from repo root, or disable `-UseBundledWheels`.
- `Open3DWheelPath does not exist: ...`
: Provide a valid wheel path relative to repo root or an absolute path.
- `wsl.exe not found. Install WSL ...`
: Install WSL and requested distro before running `-BuildOpen3DSyclWithWsl`.
- `Tests skipped because -InstallDev was not set.`
: Re-run with `-InstallDev` if you want pytest executed by bootstrap.

## After install
1. Activate environment:
```powershell
.\.venv\Scripts\Activate.ps1
```
2. Run validation:
```powershell
python -m pytest -q
```
3. Configure slicer integration:
- [OrcaSlicer integration](orcaslicer-integration.md)

## Related guides
- [Installation](installation.md)
- [Troubleshooting](troubleshooting.md)
- [Pipeline stages reference](../02-technical-reference/pipeline-stages.md)
- [FAQ](../04-reference/faq.md)
