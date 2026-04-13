# Wheelhouse Artifacts

This folder is used for generated wheelhouse outputs during release preparation.

## Why wheels are not committed

Wheel files and wheelhouse zip bundles are build artifacts, not source files.
They are intentionally excluded from git because:

- they are large (often hundreds of MB each),
- GitHub repository file limits are exceeded by some wheels,
- release assets are the canonical distribution channel.

## Distribution model

Wheelhouses are produced by CI in `.github/workflows/windows-aio-release.yml` and published as:

- `Ultra_Optimizer-Wheelhouse-windows-py312-<version>.zip`
- `Ultra_Optimizer-Wheelhouse-linux-py312-<version>.zip`

Each bundle includes `SHA256SUMS.txt`.

## Local generation examples

From repository root:

```bash
# Windows CPython 3.12 wheelhouse
python -m pip download --dest wheels/windows-py312 --only-binary=:all: --platform win_amd64 --implementation cp --python-version 312 --abi cp312 -r requirements.txt
python -m pip download --dest wheels/windows-py312 --only-binary=:all: --platform win_amd64 --implementation cp --python-version 312 --abi cp312 -r requirements-optional.txt
python -m pip download --dest wheels/windows-py312 --only-binary=:all: --platform win_amd64 --implementation cp --python-version 312 --abi cp312 -r requirements-dev.txt

# Linux CPython 3.12 wheelhouse
python -m pip download --dest wheels/linux-current --only-binary=:all: --platform manylinux_2_31_x86_64 --platform manylinux2014_x86_64 --implementation cp --python-version 312 --abi cp312 -r requirements.txt
python -m pip download --dest wheels/linux-current --only-binary=:all: --platform manylinux_2_31_x86_64 --platform manylinux2014_x86_64 --implementation cp --python-version 312 --abi cp312 -r requirements-optional.txt
python -m pip download --dest wheels/linux-current --only-binary=:all: --platform manylinux_2_31_x86_64 --platform manylinux2014_x86_64 --implementation cp --python-version 312 --abi cp312 -r requirements-dev.txt
```
