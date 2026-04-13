# Dependency License Inventory

This page tracks third-party dependency licenses used by this repository.

## Scope
- Manifest sources:
  - `requirements.txt`
  - `requirements-optional.txt`
  - `requirements-dev.txt`
  - `requirements-windows.txt`
  - `GCodeZAA/pyproject.toml`
- Snapshot date for installed metadata in this repo environment: 2026-04-13.

## Direct dependency matrix

| Component | Package | Source | License metadata | Notes |
|---|---|---|---|---|
| Core runtime | `numpy` | `requirements.txt` | `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0` | Include upstream notices in distributions. |
| Optional Stage 2 | `open3d` | `requirements-optional.txt` | `MIT` | Optional dependency, but required for full Stage 2 raycasting path. |
| Dev/testing | `pytest` | `requirements-dev.txt` | `MIT` | Test framework only. |
| Dev hooks | `pre-commit` | `requirements-dev.txt` | `MIT` | Tooling only, not runtime path. |
| Dev lint | `ruff` | `requirements-dev.txt` | `MIT` | Tooling only, not runtime path. |
| GCodeZAA runtime | `scikit-learn` | `GCodeZAA/pyproject.toml` | `BSD-3-Clause` | Upstream package dependency. |
| GCodeZAA runtime | `PyYAML` | `GCodeZAA/pyproject.toml` | `MIT` | Upstream package dependency. |
| GCodeZAA runtime | `addict` | `GCodeZAA/pyproject.toml` | `UNKNOWN` (metadata field empty) | Requires explicit upstream license verification before release. |
| GCodeZAA runtime | `Pillow` | `GCodeZAA/pyproject.toml` | `MIT-CMU` | Include copyright/license notice. |
| GCodeZAA runtime | `pandas` | `GCodeZAA/pyproject.toml` | `BSD 3-Clause License` | Include upstream notices in distributions. |
| GCodeZAA runtime | `tqdm` | `GCodeZAA/pyproject.toml` | `MPL-2.0 AND MIT` | Preserve MPL notice obligations for distribution. |

## First-party licensing
- Project root `LICENSE`: GPL-3.0 text.
- `GCodeZAA/pyproject.toml` license field: `GPL-3.0-or-later`.

## Binary/tooling licensing note
- `ArcWelder.exe` can be included in Windows AIO artifacts when present.
- Release owners must verify ArcWelder upstream license terms and bundle required notices if redistribution is enabled.

## GPL compatibility review summary

| Component | License metadata | GPL-3.0 distribution compatibility review | Status |
|---|---|---|---|
| `numpy` | BSD/MIT/Zlib/0BSD/CC0 expressions | Permissive family licenses are generally compatible with GPL redistribution when notices are preserved. | Reviewed |
| `open3d` | MIT | MIT is generally compatible with GPL redistribution when copyright/license notices are preserved. | Reviewed |
| `ArcWelder.exe` | external binary (license must be verified per source) | Compatibility depends on verified upstream license and redistribution terms of the exact binary source used. | Conditional / release-blocking until verified |

Release rule for ArcWelder:
1. Record exact source URL/path and version for bundled executable.
2. Verify upstream redistribution terms.
3. Bundle required notices with release assets.

## Transitive dependency inventory workflow
Generate reproducible transitive license evidence before release:

```bash
python -m pip install --upgrade pip
python -m pip install pip-licenses pipdeptree

mkdir -p perf_runs/license_inventory
python -m pip freeze > perf_runs/license_inventory/requirements-lock.txt
pipdeptree --warn silence > perf_runs/license_inventory/dependency-tree.txt
pip-licenses --format=markdown --with-urls --output-file perf_runs/license_inventory/licenses.md
```

## Release rule
Do not cut a release artifact until:
1. No runtime dependency has unresolved license classification.
2. Required third-party notices are included.
3. Source-availability obligations for GPL distribution are documented and satisfied.
