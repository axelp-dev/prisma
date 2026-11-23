#!/usr/bin/env bash

# Generate PDF reports for all simulation
# and trajectory CSV files

TRAJ_DIR="data/trajectories"
RESULTS_DIR="data/results"

# Generating for trajectories
for file in "$TRAJ_DIR"/*.csv; do
  echo prisma trajectory show -i "$file"
done

for file in "$RESULTS_DIR"/**/*.csv; do
  prisma simulation show -i "$file"
done
