# FAQ

## Why is Stage 2 sometimes skipped?
Stage 2 needs GCodeZAA import support and an STL file in `stl_models/`.

## Why are some comments missing after processing?
ArcWelder (Stage 3) rewrites output and strips comments.

## Do I need Open3D?
Only for full STL raycasting workflows. Core pipeline still runs without it.

## How do I install everything on Windows in one step?
Use the bootstrap installer:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev
```
This creates a venv, installs packages, checks ArcWelder, and can run tests.

## Which test command should I use?
Use:
```bash
python -m pytest -q
```
