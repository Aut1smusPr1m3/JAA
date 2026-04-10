# Contributing

## Branching
- Use feature branches from `main`.
- Open PRs targeting `main`.

## Requirements
- Python 3.11 or 3.12.
- Install dev dependencies when running tests/lint locally.

## Validation
```bash
python -m pytest -q
```

## Documentation requirements
- Keep docs in `docs/` synchronized with runtime behavior.
- Update these pages when pipeline behavior changes:
  - `docs/02-technical-reference/pipeline-stages.md`
  - `docs/01-user-guides/troubleshooting.md`
  - `docs/04-reference/faq.md`

## Notes
- ArcWelder tests are Windows-specific and skipped on non-Windows.
- Open3D is optional; code must degrade gracefully when missing.
