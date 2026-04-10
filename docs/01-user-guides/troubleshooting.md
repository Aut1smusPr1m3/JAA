# Troubleshooting

## No visible Z smoothing
Check:
1. `stl_models/` contains at least one `.stl` file.
2. Stage 2 logs show selected STL model.
3. GCodeZAA import succeeded in logs.

## Ironing not behaving as expected
Check:
1. Input G-code contains slicer `;TYPE:` markers.
2. Stage 2 actually executed (not skipped).
3. Output after Stage 3 may not keep comments (ArcWelder strips comments).

## Stage 2 skipped
Common reasons:
- GCodeZAA import failure
- missing `stl_models/` directory
- no `.stl` files in `stl_models/`

## ArcWelder skipped
Reason:
- `ArcWelder.exe` missing from repository root.

## Validate quickly
```bash
python -m pytest -q
```
