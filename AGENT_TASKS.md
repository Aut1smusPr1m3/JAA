# Agent Tasks and Autonomous Development Templates

This file provides clear task templates for AI agents and human collaborators working on the repository.

## Repository Facts

- Root files: `Ultra_Optimizer.py`, `zaa_enhanced.py`, `requirements.txt`
- Local environment: `Optimizer/` is excluded from source control
- CI command: `python -m pytest -q`
- Primary workflow: `.github/workflows/python-package.yml`
- Backup workflow: `.github/workflows/autonomous-backup.yml`
- Dependency automation: `.github/dependabot.yml`
- Issue lifecycle automation: `.github/workflows/stale-issues.yml`

## Common Task Types

### 1. Bug Fix

Goal: fix a failing behavior or incorrect output.

Steps:
1. Reproduce the bug with a minimal test case.
2. Add or update a test in `test_*.py` that captures the bug.
3. Fix the code in the relevant Python file.
4. Run `python -m pytest -q`.
5. Commit with a clear message and open a PR.

### 2. Feature Request

Goal: add a new capability or improve existing behavior.

Steps:
1. Confirm the requested behavior is compatible with the existing pipeline.
2. Add tests or examples for the feature.
3. Update docs in `README.md`, `AGENTS.md`, or other relevant docs.
4. Run `python -m pytest -q`.
5. Open a PR with a feature summary and testing notes.

### 3. Documentation Update

Goal: improve or expand repository documentation.

Steps:
1. Edit the relevant `.md` file.
2. Ensure the text is clear and actionable.
3. No code change may be required, but if docs describe commands, verify those commands still work.
4. Commit and open a PR.

### 4. Dependency Update

Goal: update project or tooling dependencies.

Steps:
1. Accept Dependabot PRs or manually update `requirements.txt` / `requirements-dev.txt`.
2. Run `pip install -r requirements.txt` or `pip install -r requirements-dev.txt`.
3. Run `python -m pytest -q`.
4. Document the dependency change in the PR.

### 5. Backup and Recovery Validation

Goal: verify the backup workflow is functioning.

Steps:
1. Open the backup workflow in GitHub Actions.
2. Confirm scheduled or manual runs succeed.
3. Verify the generated artifact and/or tag exist.
4. If a failure occurs, update `.github/workflows/autonomous-backup.yml` and rerun.

## Task Handoff Template

Use this template when assigning a task to an agent or collaborator.

```
Task: <bug fix | feature | doc update | dependency update | backup validation>
Target files: <list of files>
Goal: <short description>
Steps:
  - <step 1>
  - <step 2>
  - <step 3>
Validation:
  - Run `python -m pytest -q`
  - Confirm file changes with `git diff`
  - Verify CI workflow passes
```

## Agent Guidance

- Do not modify or commit the `Optimizer/` directory.
- Prefer changes to root Python files and markdown documentation.
- Keep commits and PR descriptions concise.
- Use GitHub issue and PR templates where available.
