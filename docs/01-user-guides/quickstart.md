# Quickstart (5 Minutes)

This is the fastest path to a first successful run.

## 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Optional full Stage 2 support:

```bash
pip install -r requirements-optional.txt
```

## 2. Prepare required files
- Put your input `.gcode` file somewhere accessible.
- Put at least one `.stl` file in `stl_models/` if you want Stage 2 surface processing.
- Put `ArcWelder.exe` in repo root if you want Stage 3 arc compression.

## 3. Run the optimizer

```bash
python Ultra_Optimizer.py path/to/input.gcode
```

## 4. Confirm success in logs
Check `kinematic_engine.log` for:
1. Stage 1 complete.
2. Stage 2 complete (or clearly skipped with reason).
3. Stage 3 complete (or skipped if ArcWelder not present).

## 5. If something looks wrong
- Stage 2 skipped or misaligned: see [Troubleshooting](troubleshooting.md).
- OrcaSlicer setup details: see [OrcaSlicer integration](orcaslicer-integration.md).
- Pipeline behavior details: see [Pipeline stages reference](../02-technical-reference/pipeline-stages.md).
