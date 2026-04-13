# License Compliance Checklist

Use this checklist before publishing a release artifact.

## Policy baseline
- Project license: GPL-3.0-or-later policy for repository distributions.
- Third-party inventory source: [Dependency license inventory](../04-reference/dependency-licenses.md).

## Checklist

### 1. Legal artifacts in repo
- [ ] Root `LICENSE` exists and matches intended project policy.
- [ ] `README.md` and docs reference the active project license.
- [ ] Any redistributable binary (for example `ArcWelder.exe`) has verified redistribution terms.

### 2. Dependency evidence
- [ ] Direct dependency licenses reviewed from requirements and `GCodeZAA/pyproject.toml`.
- [ ] Transitive dependency license snapshot generated for this release.
- [ ] No unresolved runtime dependency license remains (for example metadata marked unknown without manual verification).

### 3. Release bundle contents
- [ ] Include `LICENSE` in release zip/assets.
- [ ] Include dependency notice/inventory document in release docs or release notes.
- [ ] Keep a copy of dependency lock snapshot (`requirements-lock.txt`) with release evidence.

### 4. GPL source-availability obligations
- [ ] Release notes identify source repository and tag/commit for binaries.
- [ ] If any binary is distributed, corresponding source for covered GPL components is publicly accessible.
- [ ] Any local modifications to bundled third-party GPL-covered components are documented.

### 5. Validation gate
- [ ] `python -m pytest -q` passes before tagging.
- [ ] Windows AIO workflow inputs and docs are in sync.

## Evidence capture commands

```bash
python -m pytest -q

python -m pip install pip-licenses pipdeptree
mkdir -p perf_runs/license_inventory
python -m pip freeze > perf_runs/license_inventory/requirements-lock.txt
pipdeptree --warn silence > perf_runs/license_inventory/dependency-tree.txt
pip-licenses --format=markdown --with-urls --output-file perf_runs/license_inventory/licenses.md
```

## Related docs
- [Windows AIO release](release-aio.md)
- [Dependency license inventory](../04-reference/dependency-licenses.md)
