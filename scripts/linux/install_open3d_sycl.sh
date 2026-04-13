#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "[ERROR] This installer targets Linux hosts only."
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "[ERROR] python was not found on PATH."
  exit 1
fi

if [[ -f /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    echo "[WARN] Open3D SYCL wheels are tested upstream on Ubuntu 22.04+; current distro is ${ID:-unknown}."
  fi
fi

py_tag="$(python - <<'PY'
import sys
print(f"cp{sys.version_info.major}{sys.version_info.minor}")
PY
)"

case "$py_tag" in
  cp310|cp311|cp312|cp313|cp314)
    ;;
  *)
    echo "[ERROR] Unsupported Python tag '$py_tag'. Expected Python 3.10-3.14 for current Open3D SYCL wheels."
    exit 1
    ;;
esac

wheel_version="${OPEN3D_SYCL_VERSION:-0.19.0}"
wheel_base_url="${OPEN3D_SYCL_BASE_URL:-https://github.com/isl-org/Open3D/releases/download/main-devel}"
default_wheel_url="${wheel_base_url}/open3d_xpu-${wheel_version}-${py_tag}-${py_tag}-manylinux_2_31_x86_64.whl"
wheel_url="${OPEN3D_SYCL_WHEEL_URL:-$default_wheel_url}"

echo "[INFO] Installing Open3D SYCL wheel: ${wheel_url}"
python -m pip install --upgrade pip

# Avoid mixed CPU/SYCL Open3D installs.
python -m pip uninstall -y open3d open3d-cpu open3d-gpu open3d_xpu >/dev/null 2>&1 || true
python -m pip install "$wheel_url"

python - <<'PY'
import open3d as o3d

if not hasattr(o3d.core, "sycl"):
    raise SystemExit("[ERROR] Installed Open3D runtime does not expose SYCL backend.")

devices = [str(d) for d in o3d.core.sycl.get_available_devices()]
gpu_devices = [d for d in devices if "gpu" in d.lower()]
sycl0_available = bool(o3d.core.sycl.is_available(o3d.core.Device("SYCL:0")))

print(f"[INFO] SYCL devices: {devices if devices else 'none'}")
print(f"[INFO] SYCL:0 available: {sycl0_available}")
print(f"[INFO] SYCL GPU candidates: {gpu_devices if gpu_devices else 'none'}")

if not sycl0_available or not gpu_devices:
    raise SystemExit(
        "[WARN] No usable SYCL GPU detected. Install the correct GPU drivers/runtime. "
        "For Intel raycasting, install intel-level-zero-gpu-raytracing."
    )

print("[SUCCESS] Open3D SYCL runtime appears ready for GPU raycasting.")
PY

echo "[INFO] Optional: set SYCL_CACHE_PERSISTENT=1 to reduce first-run JIT overhead."
