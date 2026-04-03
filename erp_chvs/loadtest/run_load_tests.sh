#!/usr/bin/env bash
set -euo pipefail

HOST_URL="${1:-http://localhost:8000}"
OUT_DIR="${2:-loadtest/reports}"
SPAWN_RATE="${3:-5}"

timestamp="$(date +%Y%m%d-%H%M%S)"
run_dir="${OUT_DIR}/${timestamp}"
mkdir -p "${run_dir}"

run_locust() {
  local name="$1"
  local users="$2"
  local runtime="$3"
  local tags="$4"
  local suite="$5"

  echo "==> Ejecutando ${name} (users=${users}, runtime=${runtime}, tags=${tags})"
  export LT_SUITE="${suite}"
  python -m locust \
    -f loadtest/locustfile.py \
    --headless \
    --host "${HOST_URL}" \
    -u "${users}" \
    -r "${SPAWN_RATE}" \
    --run-time "${runtime}" \
    --tags "${tags}" \
    --html "${run_dir}/${name}.html" \
    --csv "${run_dir}/${name}"
}

echo "Directorio de salida: ${run_dir}"
echo "Host: ${HOST_URL}"

run_locust "baseline-core-u05" 5  "3m"  "core" "core"
run_locust "baseline-core-u10" 10 "3m"  "core" "core"
run_locust "baseline-core-u20" 20 "4m"  "core" "core"
run_locust "baseline-core-u30" 30 "5m"  "core" "core"

run_locust "stress-core-u40"   40 "4m"  "core" "core"
run_locust "stress-core-u50"   50 "4m"  "core" "core"

run_locust "heavy-u03"         3  "6m"  "heavy" "heavy"
run_locust "ia-u05"            5  "5m"  "ia" "ia"

run_locust "soak-core-u30"     30 "20m" "core" "core"

echo "Listo. Reportes generados en: ${run_dir}"
