#!/usr/bin/env bash

#     Launch all presets simulation on generated trajectories.

TRAJ_DIR="data/trajectories"
RESULTS_DIR="data/results"

# Ouput dirs mapping
PRESETS=("glycerol_bead" "statolith")

for preset in "${PRESETS[@]}"; do
  mkdir -p "$RESULTS_DIR/$preset"

  for traj_file in "$TRAJ_DIR"/*.csv; do
    filename="${traj_file##*/}"
    base_name="${filename%.csv}"

    out_csv="$RESULTS_DIR/$preset/${base_name}.csv"

    echo "--------------------------------------------------------"
    echo "[INFO] Simulating : $preset ($base_name)"
    prisma simulation launch -i "$traj_file" \
      -o "$out_csv" \
      -p "$preset" \
      --log-report
  done
done
