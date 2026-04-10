#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INPUT_GCODE="${1:-$ROOT_DIR/Gcode just for testing/3DBenchy_PLA_35m37s.gcode}"
MODEL_STL="${2:-$ROOT_DIR/stl_models/3DBenchy.stl}"
OUT_ROOT="${3:-$ROOT_DIR/perf_runs/benchy}"

if [[ ! -f "$INPUT_GCODE" ]]; then
  echo "ERROR: input G-code not found: $INPUT_GCODE" >&2
  exit 1
fi

if [[ ! -f "$MODEL_STL" ]]; then
  echo "ERROR: STL model not found: $MODEL_STL" >&2
  exit 1
fi

python - <<'PY'
import importlib
mods = ["open3d", "numpy", "pytest"]
missing = []
for m in mods:
    try:
        importlib.import_module(m)
    except Exception:
        missing.append(m)
if missing:
    raise SystemExit("Missing required packages: " + ", ".join(missing))
PY

ts="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$OUT_ROOT/$ts"
mkdir -p "$RUN_DIR"

WORK_GCODE="$RUN_DIR/benchy_input_work.gcode"
cp "$INPUT_GCODE" "$WORK_GCODE"

export GCODEZAA_SAMPLE_DISTANCE_MM="${GCODEZAA_SAMPLE_DISTANCE_MM:-0.2}"
export GCODEZAA_MAX_SEGMENT_SAMPLES="${GCODEZAA_MAX_SEGMENT_SAMPLES:-192}"
export GCODEZAA_BATCH_RAY_SIZE="${GCODEZAA_BATCH_RAY_SIZE:-4096}"

export ULTRA_OPTIMIZER_PROFILE=1
export ULTRA_OPTIMIZER_PROFILE_OUT="$RUN_DIR/ultra_optimizer_profile.prof"

LOG_FILE="$RUN_DIR/optimizer.log"
SUMMARY_FILE="$RUN_DIR/summary.txt"

start_epoch="$(date +%s)"
(
  cd "$ROOT_DIR"
  python Ultra_Optimizer.py "$WORK_GCODE"
) >"$LOG_FILE" 2>&1
end_epoch="$(date +%s)"
wall_seconds="$((end_epoch - start_epoch))"

RUN_DIR="$RUN_DIR" \
INPUT_GCODE="$INPUT_GCODE" \
WORK_GCODE="$WORK_GCODE" \
MODEL_STL="$MODEL_STL" \
LOG_FILE="$LOG_FILE" \
WALL_SECONDS="$wall_seconds" \
python - <<'PY' > "$SUMMARY_FILE"
import os
from pathlib import Path

from Ultra_Optimizer import MIN_BUILDPLATE_Z, count_negative_z_commands

run_dir = Path(os.environ["RUN_DIR"])
input_gcode = Path(os.environ["INPUT_GCODE"])
work_gcode = Path(os.environ["WORK_GCODE"])
model_stl = Path(os.environ["MODEL_STL"])
log_path = Path(os.environ["LOG_FILE"])
profile_path = run_dir / "ultra_optimizer_profile.prof"

neg = count_negative_z_commands(str(work_gcode), MIN_BUILDPLATE_Z)
print(f"run_dir={run_dir}")
print(f"input_gcode={input_gcode}")
print(f"work_gcode={work_gcode}")
print(f"model_stl={model_stl}")
print(f"wall_seconds={int(os.environ['WALL_SECONDS'])}")
print(f"sample_distance_mm={os.environ['GCODEZAA_SAMPLE_DISTANCE_MM']}")
print(f"max_segment_samples={os.environ['GCODEZAA_MAX_SEGMENT_SAMPLES']}")
print(f"batch_ray_size={os.environ['GCODEZAA_BATCH_RAY_SIZE']}")
print(f"negative_z_commands={neg}")
print(f"profile_exists={profile_path.exists()}")
print(f"profile_size_bytes={profile_path.stat().st_size if profile_path.exists() else 0}")
print(f"log_exists={log_path.exists()}")
PY

echo "Benchy profiling run complete"
echo "Run directory: $RUN_DIR"
echo "Summary: $SUMMARY_FILE"
echo "Log: $LOG_FILE"
echo "Profile: $RUN_DIR/ultra_optimizer_profile.prof"
cat "$SUMMARY_FILE"
