# Testing

## Run all tests
```bash
python -m pytest -q
```

## Current status expectation
- tests pass on Linux without Open3D installed,
- Windows-only ArcWelder tests are skipped outside Windows.

## CI matrix
- GitHub Actions runs Python 3.11 and 3.12.
- Each Python version runs in two lanes:
	- without Open3D,
	- with Open3D installed.

## Notes
Some historical tests still return boolean values instead of pure assertion style; pytest will emit warnings, but test pass/fail remains valid.

## Stage 2 evidence capture
Use the helper script to capture repeatable Stage 2 diagnostics for merge/release readiness:

```bash
./scripts/perf/capture_stage2_evidence.sh
```

Outputs are written under `perf_runs/stage2_evidence/<timestamp>/` and include:
- full optimizer log,
- an evidence summary with:
	- Stage 2 env snapshot lines,
	- raycast device resolution lines,
	- counts and samples for:
		- `Segment sampling capped`,
		- `Skipping surface-following for implausible segment`,
		- `Surface-follow state jump candidate`.
