#!/usr/bin/env bash
set -euo pipefail

# Usage: ./generate_trajectories.sh [debug|prod] [--clean]
MODE="${1:-debug}"
CLEAN_FLAG="${2:-}"
DATA_DIR="data/trajectories"
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/generate_trajectories_${MODE}.log"

if [[ "$MODE" != "debug" && "$MODE" != "prod" ]]; then
  echo "[ERROR] Invalid mode '$MODE'. Usage: $0 [debug|prod] [--clean]"
  exit 1
fi

mkdir -p "$DATA_DIR" "$LOG_DIR"
: >"$LOG_FILE"

if [[ "$CLEAN_FLAG" == "--clean" ]]; then
  rm -f "$DATA_DIR"/*.csv "$DATA_DIR"/*.pdf
fi

if [[ "$MODE" == "debug" ]]; then
  SPECS=(
    "static_1g:60:0.05:1m"
    "clinostat_1d:60:0.05:1m"
    "centrifuge_sweep:120:0.05:2m"
    "desynchronized_sine:120:0.05:2m"
    "constant_speed_ratio:180:0.05:3m"
    "random_walk:300:0.05:5m"
  )
else
  SPECS=(
    "static_1g:7200:0.1:2h"
    "clinostat_1d:300:0.02:5m"
    "centrifuge_sweep:300:0.02:5m"
    "desynchronized_sine:600:0.02:10m"
    "constant_speed_ratio:900:0.02:15m"
    "random_walk:1800:0.02:30m"
  )
fi

echo "PRISMA Trajectory Batch Generation (mode: $MODE)"
echo "Detailed logs -> $LOG_FILE"
echo "--------------------------------------------------------"

FAILED=0

for spec in "${SPECS[@]}"; do
  IFS=":" read -r profile duration step tag <<<"$spec"
  out_csv="$DATA_DIR/${profile}_${MODE}_${tag}.csv"
  desc="Preset ${profile} (${MODE} mode, ${tag}) generated for PRISMA validation"

  printf "  %-24s (%4ss @ dt=%-4ss) ... " "$profile" "$duration" "$step"

  {
    echo "========================================================"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Profile: $profile | Duration: ${duration}s | Step: ${step}s"
    echo "========================================================"
  } >>"$LOG_FILE"

  if prisma trajectory generate \
    -o "$out_csv" \
    -p "$profile" \
    -d "$duration" \
    -s "$step" \
    -t "$desc" \
    -l >>"$LOG_FILE" 2>&1; then
    echo "OK"
  else
    echo "FAILED (see $LOG_FILE)"
    FAILED=$((FAILED + 1))
  fi
done

echo "--------------------------------------------------------"
if [[ "$FAILED" -eq 0 ]]; then
  echo "Done: all ${#SPECS[@]} trajectories generated cleanly."
else
  echo "Completed with $FAILED error(s). Inspect $LOG_FILE for details."
  exit 1
fi
