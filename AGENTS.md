# Agent and Repo Workflow Guide

## Purpose
This repository contains `Ultra_Optimizer` and supporting integration code for OrcaSlicer post-processing and arc optimization.

## Core files
- `Ultra_Optimizer.py` — main post-processing entry point
- `zaa_enhanced.py` — Z-Anti-Aliasing helper
- `ArcWelder.exe` — arc compression tool used by the repo
- `requirements.txt` — Python dependency list
- `README.md` — project overview and setup instructions
- `test_*.py` — unit and integration tests
- `.github/workflows/python-package.yml` — CI workflow

## Setup
1. Use a Python 3.11 or 3.12 interpreter.
2. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Run tests:
   ```bash
   python -m pytest -q
   ```

## GitHub workflow
- Primary branch: `main`
- All pull requests should trigger CI via `.github/workflows/python-package.yml`
- Use issue templates for bug reports and feature requests
- Use the PR template for consistent merge readiness

## Agent guidance
When assisting with this repository, agents should:
- Focus on `Ultra_Optimizer.py`, `zaa_enhanced.py`, and tests in the repository root
- Avoid editing the `Optimizer/` directory, which is a local Python environment
- Keep changes limited to source, docs, and CI/support metadata
- Use `pytest` as the verification command for code changes

## Recommended editor extensions
- `ms-python.python`
- `GitHub.copilot-chat`
