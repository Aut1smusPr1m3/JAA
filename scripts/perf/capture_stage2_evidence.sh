#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INPUT_GCODE="${1:-$ROOT_DIR/Gcode just for testing/3DBenchy_PLA_35m37s.gcode}"
OUT_ROOT="${2:-$ROOT_DIR/perf_runs/stage2_evidence}"

if [[ ! -f "$INPUT_GCODE" ]]; then
  echo "ERROR: input G-code not found: $INPUT_GCODE" >&2
  exit 1
fi

ts="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="$OUT_ROOT/$ts"
mkdir -p "$RUN_DIR"

WORK_GCODE="$RUN_DIR/input_work.gcode"
cp "$INPUT_GCODE" "$WORK_GCODE"

export GCODEZAA_SAMPLE_DISTANCE_MM="${GCODEZAA_SAMPLE_DISTANCE_MM:-0.2}"
export GCODEZAA_MAX_SEGMENT_SAMPLES="${GCODEZAA_MAX_SEGMENT_SAMPLES:-384}"
export GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM="${GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM:-1000}"
export GCODEZAA_BATCH_RAY_SIZE="${GCODEZAA_BATCH_RAY_SIZE:-4096}"
export GCODEZAA_RAYCAST_DEVICE="${GCODEZAA_RAYCAST_DEVICE:-auto}"
export GCODEZAA_REQUIRE_GPU="${GCODEZAA_REQUIRE_GPU:-0}"

LOG_FILE="$RUN_DIR/optimizer.log"
SUMMARY_FILE="$RUN_DIR/evidence_summary.txt"

start_epoch="$(date +%s)"
(
  cd "$ROOT_DIR"
  python Ultra_Optimizer.py "$WORK_GCODE"
) >"$LOG_FILE" 2>&1
end_epoch="$(date +%s)"
wall_seconds="$((end_epoch - start_epoch))"

capped_count="$(grep -c "Segment sampling capped" "$LOG_FILE" || true)"
skip_count="$(grep -c "Skipping surface-following for implausible segment" "$LOG_FILE" || true)"
state_jump_count="$(grep -c "Surface-follow state jump candidate" "$LOG_FILE" || true)"

{
  echo "run_dir=$RUN_DIR"
  echo "input_gcode=$INPUT_GCODE"
  echo "work_gcode=$WORK_GCODE"
  echo "wall_seconds=$wall_seconds"
  echo "GCODEZAA_SAMPLE_DISTANCE_MM=$GCODEZAA_SAMPLE_DISTANCE_MM"
  echo "GCODEZAA_MAX_SEGMENT_SAMPLES=$GCODEZAA_MAX_SEGMENT_SAMPLES"
  echo "GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM=$GCODEZAA_MAX_SURFACE_FOLLOW_SEGMENT_MM"
  echo "GCODEZAA_BATCH_RAY_SIZE=$GCODEZAA_BATCH_RAY_SIZE"
  echo "GCODEZAA_RAYCAST_DEVICE=$GCODEZAA_RAYCAST_DEVICE"
  echo "GCODEZAA_REQUIRE_GPU=$GCODEZAA_REQUIRE_GPU"
  echo "segment_sampling_capped_count=$capped_count"
  echo "implausible_segment_skip_count=$skip_count"
  echo "state_jump_candidate_count=$state_jump_count"
  echo
  echo "--- Stage 2 env snapshot lines ---"
  grep "\[GCodeZAA\] Stage 2 runtime env" "$LOG_FILE" || true
  echo
  echo "--- Device resolution lines ---"
  grep "\[GCodeZAA\] Raycast device resolved" "$LOG_FILE" || true
  echo
  echo "--- First 10 capped segment lines ---"
  grep "Segment sampling capped" "$LOG_FILE" | head -n 10 || true
  echo
  echo "--- First 10 implausible skip lines ---"
  grep "Skipping surface-following for implausible segment" "$LOG_FILE" | head -n 10 || true
  echo
  echo "--- First 10 state jump candidate lines ---"
  grep "Surface-follow state jump candidate" "$LOG_FILE" | head -n 10 || true
} > "$SUMMARY_FILE"

echo "Stage 2 evidence capture complete"
echo "Run directory: $RUN_DIR"
echo "Summary: $SUMMARY_FILE"
echo "Log: $LOG_FILE"
cat "$SUMMARY_FILE"
