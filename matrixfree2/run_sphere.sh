#!/usr/bin/env bash
set -euo pipefail

export JAX_ENABLE_X64=True

MESH_NAME="sphere_40nm_new"
OUT_DIR="hyst_sphere_40nm_new"
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
  echo "Using existing mesh: ${MESH_NAME}.npz"
  echo

  pixi run -e cuda python - <<PY
import numpy as np
z = np.load("${MESH_NAME}.npz")
print("Mesh check:")
print("  knt:", z["knt"].shape, z["knt"].dtype)
print("  ijk:", z["ijk"].shape, z["ijk"].dtype)
print("  tags:", np.unique(z["ijk"][:, -1], return_counts=True))
PY

  echo

  pixi run -e cuda python - <<'PY'
import jax
print("JAX backend:", jax.default_backend())
print("JAX devices:", jax.devices())
PY

  echo

  SIM_START=$(date +%s)
  echo "Simulation started: $(date --iso-8601=seconds)"

  pixi run -e cuda python ../src/loop.py "${MESH_NAME}" \
    --add-shell \
    --layers 4 \
    --out-dir "${OUT_DIR}" \
    --verbose

  SIM_END=$(date +%s)
  SIM_DURATION=$((SIM_END - SIM_START))

  echo
  echo "Simulation finished: $(date --iso-8601=seconds)"
  echo "Simulation runtime: $(format_duration "${SIM_DURATION}")"

  TOTAL_END=$(date +%s)
  TOTAL_DURATION=$((TOTAL_END - TOTAL_START))

  echo
  echo "Run finished: $(date --iso-8601=seconds)"
  echo "Total runtime: $(format_duration "${TOTAL_DURATION}")"
} 2>&1 | tee "${LOG_FILE}"
