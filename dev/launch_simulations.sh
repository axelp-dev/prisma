#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

# Launch all presets simulation on generated trajectories.

TRAJ_DIR="data/trajectories"
RESULTS_DIR="data/results"
LOG_FILE="data/results/simulations.log"
PRESETS=("glycerol_bead" "statolith")

mkdir -p "$RESULTS_DIR"

# Ask for cleaning
read -r -p "Supprimer toutes les anciennes simulations dans '$RESULTS_DIR' ? [o/N] " response
if [[ "$response" =~ ^([oO][uU][iI]|[oO]|[yY][eE][sS]|[yY])$ ]]; then
  echo "[INFO] Nettoyage des anciens résultats..."
  for preset in "${PRESETS[@]}"; do
    rm -rf "${RESULTS_DIR:?}/${preset:?}"
  done
  rm -f "$LOG_FILE"
else
  echo "[INFO] Conservation des simulations existantes."
fi

# Reinit log file
{
  echo "=== Lancement des simulations : $(date '+%Y-%m-%d %H:%M:%S') ==="
} >>"$LOG_FILE"

# Simulation loop
for preset in "${PRESETS[@]}"; do
  mkdir -p "$RESULTS_DIR/$preset"
  echo "========================================================"
  echo "[PRESET] $preset"

  for traj_file in "$TRAJ_DIR"/*.csv; do
    filename="${traj_file##*/}"
    base_name="${filename%.csv}"

    out_csv="$RESULTS_DIR/$preset/${base_name}.csv"
    out_pdf="$RESULTS_DIR/$preset/${base_name}.pdf"

    # Check if CSV and PDF already exists
    if [[ -f "$out_csv" && -f "$out_pdf" ]]; then
      echo "  [SKIP] $base_name (déjà généré)"
      continue
    fi

    printf "  [RUN]  %-32s ... " "$base_name"

    # Redirect stdout & stderr into log file
    if prisma simulation launch -i "$traj_file" \
      -o "$out_csv" \
      -p "$preset" \
      --log-report >>"$LOG_FILE" 2>&1; then
      echo "[OK]"
    else
      echo "[FAIL] (voir $LOG_FILE)"
      exit 1
    fi
  done
done

echo "========================================================"
echo "[INFO] Terminé ! Logs complets disponibles dans $LOG_FILE"
