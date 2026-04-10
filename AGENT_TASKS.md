# Agent Task Templates

## Bug fix
1. Reproduce with a minimal test.
2. Patch code in smallest safe scope.
3. Add or update regression tests.
4. Run `python -m pytest -q`.

## Feature or refactor
1. Confirm existing behavior and constraints.
2. Implement incrementally with tests.
3. Update docs in `docs/`.
4. Run `python -m pytest -q`.

## Documentation update
1. Update the relevant `docs/` pages.
2. Ensure pipeline/order/optionality statements match code.
3. If behavior changed, update FAQ and troubleshooting.

## Doc cloud agents
- `DocSynth`: update docs from code/test truth.
- `DocDrift`: detect drift in behavior-changing PRs.
- `ReleaseDoc`: generate changelog/release notes.
