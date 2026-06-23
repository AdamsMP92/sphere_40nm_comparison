#!/usr/bin/env bash
set -euo pipefail

export JAX_ENABLE_X64=True

OUT_DIR="hyst_sphere_40nm_test"
LOG_FILE="${OUT_DIR}/run.log"

mkdir -p "${OUT_DIR}"

format_duration() {
  local seconds="$1"
  printf '%02d:%02d:%02d' \
    $((seconds / 3600)) \
    $(((seconds % 3600) / 60)) \
    $((seconds % 60))
}

TOTAL_START=$(date +%s)

{
  echo "Run started: $(date --iso-8601=seconds)"
  echo

  # Mesh generation
  MESH_START=$(date +%s)
  echo "Mesh generation started: $(date --iso-8601=seconds)"

  pixi run -e cuda python ../src/mesh.py \
    --geom ellipsoid \
    --extent 40,40,40 \
    --h 2.0 \
    --backend meshpy \
    --out-name sphere_40nm

  MESH_END=$(date +%s)
  MESH_DURATION=$((MESH_END - MESH_START))

  echo "Mesh generation finished: $(date --iso-8601=seconds)"
  echo "Mesh generation runtime: $(format_duration "${MESH_DURATION}")"
  echo

  # Hysteresis simulation
  SIM_START=$(date +%s)
  echo "Simulation started: $(date --iso-8601=seconds)"

  pixi run -e cuda python ../src/loop.py sphere_40nm \
    --add-shell \
    --layers 4 \
    --out-dir "${OUT_DIR}" \
    --verbose

  SIM_END=$(date +%s)
  SIM_DURATION=$((SIM_END - SIM_START))

  echo "Simulation finished: $(date --iso-8601=seconds)"
  echo "Simulation runtime: $(format_duration "${SIM_DURATION}")"
  echo

  # Plotting
  PLOT_START=$(date +%s)
  echo "Plotting started: $(date --iso-8601=seconds)"

  pixi run -e cuda python ../src/plot_hysteresis.py \
    "${OUT_DIR}/hysteresis.csv" \
    "${OUT_DIR}/sphere_hyst.png"

  PLOT_END=$(date +%s)
  PLOT_DURATION=$((PLOT_END - PLOT_START))

  echo "Plotting finished: $(date --iso-8601=seconds)"
  echo "Plotting runtime: $(format_duration "${PLOT_DURATION}")"
  echo

  TOTAL_END=$(date +%s)
  TOTAL_DURATION=$((TOTAL_END - TOTAL_START))

  echo "Run finished: $(date --iso-8601=seconds)"
  echo "Total runtime: $(format_duration "${TOTAL_DURATION}")"
} 2>&1 | tee "${LOG_FILE}"
