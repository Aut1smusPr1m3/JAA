# Ultra_Optimizer Documentation

This documentation matches the current repository behavior.

## Quick paths
- 5-minute first run: [Quickstart](01-user-guides/quickstart.md)
- New user setup: [Installation](01-user-guides/installation.md)
- Windows all-in-one setup: [Windows AIO setup](01-user-guides/windows-aio-setup.md)
- OrcaSlicer integration: [OrcaSlicer setup](01-user-guides/orcaslicer-integration.md)
- Troubleshooting: [Troubleshooting](01-user-guides/troubleshooting.md)
- Internal pipeline details: [Pipeline stages](02-technical-reference/pipeline-stages.md)
- Architecture map: [Architecture map](02-technical-reference/architecture-map.md)
- Configuration reference: [Configuration](02-technical-reference/configuration.md)
- FAQ: [FAQ](04-reference/faq.md)
- Dependency licenses: [Dependency license inventory](04-reference/dependency-licenses.md)
- Developer workflow: [Testing](03-development/testing.md)
- Release packaging: [Windows AIO release](03-development/release-aio.md)
- Release compliance: [License compliance checklist](03-development/license-compliance.md)
- Installer review: [Windows bootstrap audit](03-development/windows-bootstrap-audit.md)
- Agent automation: [Doc agents](03-development/doc-agents.md)

## What runs today
- Stage 1 always runs: kinematic optimization + M204 acceleration tuning.
- Stage 2 runs only when GCodeZAA is importable and STL files exist in `stl_models/`.
- Stage 3 runs only when `ArcWelder.exe` exists next to `Ultra_Optimizer.py`.

## Critical warnings
- Run the post-processor in the correct virtual environment. Using a different Python interpreter is a common cause of missing dependency behavior.
- Enable verbose G-code output in OrcaSlicer so feature/ironing comments are preserved.
- Disable Arc fitting in OrcaSlicer. Let Stage 3 (ArcWelder) handle arc conversion.
- Verify and tune `MAX_SMOOTHING_ANGLE` for your specific printer clearance.
- For moved or rotated models, ensure transform metadata is present in the G-code so Stage 2 aligns the STL correctly. See [OrcaSlicer integration](01-user-guides/orcaslicer-integration.md) for hint format.

## Source of truth files
- `Ultra_Optimizer.py`
- `GCodeZAA/gcodezaa/process.py`
- `GCodeZAA/gcodezaa/surface_analysis.py`
- `test_*.py`
