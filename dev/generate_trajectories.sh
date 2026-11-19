#!/usr/bin/env bash
set -e

DATA_DIR="data/trajectories"
DURATION=600
STEP=0.01

mkdir -p "$DATA_DIR"

# Clean old files
echo "[INFO] Cleaning $DATA_DIR..."
rm -f "$DATA_DIR"/*.csv "$DATA_DIR"/*.pdf

# Init supported profiles
PROFILES=(
  "random_walk"
  "desynchronized_sine"
  "constant_speed_ratio"
  "static_1g"
  "clinostat_1d"
  "centrifuge_sweep"
)

# Loop generation
for profile in "${PROFILES[@]}"; do
  out_csv="$DATA_DIR/${profile}_10m.csv"
  desc="Preset ${profile} profile generated for refactor validation"
  
  echo "--------------------------------------------------------"
  echo "[INFO] Generating : $profile"
  prisma trajectory generate \
    -o "$out_csv" \
    -p "$profile" \
    -d "$DURATION" \
    -s "$STEP" \
    -t "$desc" \
    -l
done

echo "--------------------------------------------------------"
echo "[INFO] All trajectories generated into $DATA_DIR !"