# Agent Workflow Guide

## Core guidance
- Prioritize `Ultra_Optimizer.py`, `GCodeZAA/gcodezaa/`, and `test_*.py`.
- Keep changes limited to source, tests, docs, and CI metadata.
- Avoid modifying local virtual-environment artifacts.

## Validation command
```bash
python -m pytest -q
```

## Documentation workflow
- Docs source now lives in `docs/`.
- Doc automation agent specs live in `.copilot/agents/`.
- See [docs/03-development/doc-agents.md](docs/03-development/doc-agents.md).
