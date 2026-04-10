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
