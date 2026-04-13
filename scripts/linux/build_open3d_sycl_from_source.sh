#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPEN3D_REF="${OPEN3D_REF:-v0.19.0}"
OPEN3D_SRC_DIR="${OPEN3D_SRC_DIR:-$ROOT_DIR/.cache/open3d-src}"
OPEN3D_BUILD_DIR="${OPEN3D_BUILD_DIR:-$ROOT_DIR/.cache/open3d-build-sycl}"
PYTHON_EXE="${PYTHON_EXE:-python}"

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "[ERROR] Open3D SYCL source build is Linux-only in upstream Open3D."
  exit 1
fi

if ! command -v "$PYTHON_EXE" >/dev/null 2>&1; then
  echo "[ERROR] Python executable not found: $PYTHON_EXE"
  exit 1
fi

if [[ ! -f /opt/intel/oneapi/setvars.sh ]]; then
  echo "[ERROR] oneAPI setvars.sh not found at /opt/intel/oneapi/setvars.sh"
  echo "[HINT] Install Intel oneAPI Base Toolkit first."
  exit 1
fi

# shellcheck disable=SC1091
source /opt/intel/oneapi/setvars.sh >/dev/null 2>&1

for tool in git cmake make icx icpx; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "[ERROR] Missing required tool: $tool"
    exit 1
  fi
done

mkdir -p "$(dirname "$OPEN3D_SRC_DIR")"
if [[ ! -d "$OPEN3D_SRC_DIR/.git" ]]; then
  echo "[INFO] Cloning Open3D source into $OPEN3D_SRC_DIR"
  git clone --recursive https://github.com/isl-org/Open3D.git "$OPEN3D_SRC_DIR"
fi

cd "$OPEN3D_SRC_DIR"
git fetch --tags --force
if [[ -n "$OPEN3D_REF" ]]; then
  git checkout "$OPEN3D_REF"
  git submodule update --init --recursive
fi

mkdir -p "$OPEN3D_BUILD_DIR"
cd "$OPEN3D_BUILD_DIR"

echo "[INFO] Configuring Open3D SYCL build"
cmake \
  -DBUILD_SYCL_MODULE=ON \
  -DCMAKE_C_COMPILER=icx \
  -DCMAKE_CXX_COMPILER=icpx \
  -DBUILD_PYTHON_MODULE=ON \
  -DBUILD_GUI=OFF \
  -DBUILD_EXAMPLES=OFF \
  -DBUILD_UNIT_TESTS=OFF \
  "$OPEN3D_SRC_DIR"

echo "[INFO] Building Open3D"
cmake --build . -j"$(nproc)"

echo "[INFO] Installing Open3D Python package into active environment"
cmake --build . --target install-pip-package -j"$(nproc)"

"$PYTHON_EXE" - <<'PY'
import open3d as o3d

if not hasattr(o3d.core, "sycl"):
    raise SystemExit("[ERROR] Installed Open3D does not expose SYCL backend.")

devices = [str(d) for d in o3d.core.sycl.get_available_devices()]
sycl0_available = bool(o3d.core.sycl.is_available(o3d.core.Device("SYCL:0")))
print(f"[INFO] SYCL devices: {devices if devices else 'none'}")
print(f"[INFO] SYCL:0 available: {sycl0_available}")

if not sycl0_available:
    raise SystemExit(
        "[WARN] SYCL:0 unavailable after build. Install/verify GPU runtime and drivers. "
        "For Intel GPU raycasting, install intel-level-zero-gpu-raytracing."
    )

print("[SUCCESS] Open3D SYCL source build is installed and reports SYCL:0 availability.")
PY
