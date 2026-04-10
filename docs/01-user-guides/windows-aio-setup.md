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

## Default behavior
- Creates or reuses `.venv`.
- Installs `requirements.txt`.
- Installs `requirements-optional.txt` by default.
- Installs `requirements-dev.txt` when `-InstallDev` is provided.
- Ensures `ArcWelder.exe` exists in repo root.
- Creates `stl_models/` if missing.

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

- Skip tests:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev -SkipTests
```

- Custom venv path:
```powershell
./scripts/windows/bootstrap.ps1 -VenvPath ".venv-win"
```
