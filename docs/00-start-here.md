# Ultra_Optimizer Documentation

This documentation matches the current repository behavior.

## Quick paths
- New user setup: [Installation](01-user-guides/installation.md)
- Windows all-in-one setup: [Windows AIO setup](01-user-guides/windows-aio-setup.md)
- OrcaSlicer integration: [OrcaSlicer setup](01-user-guides/orcaslicer-integration.md)
- Troubleshooting: [Troubleshooting](01-user-guides/troubleshooting.md)
- Internal pipeline details: [Pipeline stages](02-technical-reference/pipeline-stages.md)
- Developer workflow: [Testing](03-development/testing.md)
- Release packaging: [Windows AIO release](03-development/release-aio.md)
- Agent automation: [Doc agents](03-development/doc-agents.md)

## What runs today
- Stage 1 always runs: kinematic optimization + M204 acceleration tuning.
- Stage 2 runs only when GCodeZAA is importable and STL files exist in `stl_models/`.
- Stage 3 runs only when `ArcWelder.exe` exists next to `Ultra_Optimizer.py`.

## Source of truth files
- `Ultra_Optimizer.py`
- `GCodeZAA/gcodezaa/process.py`
- `GCodeZAA/gcodezaa/surface_analysis.py`
- `test_*.py`
