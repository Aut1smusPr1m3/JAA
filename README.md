# Ultra_Optimizer

Ultra_Optimizer is an OrcaSlicer-focused G-code post-processor with a three-stage pipeline:

1. Stage 1 (always): kinematic optimization and M204 acceleration control.
2. Stage 2 (optional): GCodeZAA surface-aware processing when STL models are available.
3. Stage 3 (optional): ArcWelder arc compression when ArcWelder.exe is present.

## Start here
- [Documentation entry](docs/00-start-here.md)
- [Installation](docs/01-user-guides/installation.md)
- [Windows AIO setup](docs/01-user-guides/windows-aio-setup.md)
- [OrcaSlicer integration](docs/01-user-guides/orcaslicer-integration.md)
- [Troubleshooting](docs/01-user-guides/troubleshooting.md)
- [Pipeline reference](docs/02-technical-reference/pipeline-stages.md)

## Quick setup
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional full Stage 2 dependencies:
```bash
pip install -r requirements-optional.txt
```

Windows all-in-one bootstrap:
```powershell
./scripts/windows/bootstrap.ps1 -InstallDev
```

## Test
```bash
python -m pytest -q
```

## Notes
- Open3D is optional for advanced Stage 2 raycasting workflows.
- ArcWelder integration requires ArcWelder.exe in repository root.
- Runtime logs are written to `kinematic_engine.log`.
