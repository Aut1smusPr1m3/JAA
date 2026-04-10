# Contributing to Ultra_Optimizer

Thank you for contributing to this repository. These guidelines are meant to keep the project stable, maintainable, and agent-friendly.

## Branching and Workflow

- `main` is the stable release branch.
- Use feature branches named `feature/<short-description>`.
- Use bugfix branches named `bugfix/<short-description>`.
- Use docs branches named `docs/<short-description>`.
- Open a pull request against `main` for all changes.

## Commit and PR Expectations

- Keep commits small and focused.
- Add tests for bug fixes and new behavior whenever possible.
- Use descriptive commit messages.
- Reference GitHub issues when applicable.
- Ensure `git status --short` is clean before creating a PR.

## Testing

Run the test suite before opening a PR:

```powershell
python -m pytest -q
```

If you add or modify tests, confirm they pass locally.

### Optional local tooling

Install dev tooling with:

```powershell
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pre-commit install
```

Then run pre-commit checks manually with:

```powershell
pre-commit run --all-files
```

## Automation and Agent Support

This repository is built to support autonomous development. When making changes:

- Update `AGENT_TASKS.md` if the change affects the task workflow or introduces a new task type.
- Keep `AGENTS.md` current with the core files and workflow commands.
- Document any new automation, scheduled workflow, or dependency management change here.

## Dependency Management

- Base dependencies are in `requirements.txt`.
- Dev dependencies are in `requirements-dev.txt`.
- Dependabot is configured to propose dependency updates automatically.

## Troubleshooting

- Do not commit the `Optimizer/` directory or any local Python environment artifacts.
- If CI fails, inspect the GitHub Actions logs and rerun the failing tests locally.
- If a backup workflow runs, verify the artifact or tag was created in the repository.

## Files to Review

- `.github/workflows/python-package.yml`
- `.github/workflows/autonomous-backup.yml`
- `.github/dependabot.yml`
- `AGENTS.md`
- `AGENT_TASKS.md`
- `README.md`
- `requirements-dev.txt`
