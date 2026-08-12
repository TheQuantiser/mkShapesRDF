#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"

MODE="${1:-pilot}"
shift || true

case "${MODE}" in
  compile|pilot|full-local|submit|merge|summary|plots) ;;
  *)
    echo "Usage: $0 {compile|pilot|full-local|submit|merge|summary|plots}" >&2
    exit 2
    ;;
esac

if [[ -f "${REPO_ROOT}/start.sh" ]]; then
  # LCG setup scripts probe optional variables that are legitimately unset.
  set +u
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/start.sh"
fi
set -u

export PAIRING_CAMPAIGN="${PAIRING_CAMPAIGN:-pairing_$(date -u +%Y%m%d_%H%M%S)}"
export XRD_READ_ENDPOINT="${XRD_READ_ENDPOINT:-root://eoscms.cern.ch}"
export XRD_DISCOVERY_ENDPOINT="${XRD_DISCOVERY_ENDPOINT:-${XRD_READ_ENDPOINT}}"
export FILES_PER_JOB="${FILES_PER_JOB:-10}"

ERAS=(2022 2022EE 2023 2023BPix 2024)
PILOT_EVENTS="${PAIRING_PILOT_EVENTS:-20000}"
QUEUE="${PAIRING_QUEUE:-workday}"

run_compile_or_analysis() {
  local era="$1"
  local configs_dir="${SCRIPT_DIR}/configs/${PAIRING_CAMPAIGN}/${era}"
  local output_dir="${SCRIPT_DIR}/rootFiles/${PAIRING_CAMPAIGN}/${era}"
  export ERA="${era}"
  export PAIRING_CONFIGS_FOLDER="${configs_dir}"
  export PAIRING_OUTPUT_FOLDER="${output_dir}"
  export PAIRING_BATCH_FOLDER="${SCRIPT_DIR}/condor/${PAIRING_CAMPAIGN}/${era}"

  echo "[Pairing] mode=${MODE} campaign=${PAIRING_CAMPAIGN} ERA=${ERA}"
  case "${MODE}" in
    compile)
      export LIMIT_FILES_PER_SAMPLE="${LIMIT_FILES_PER_SAMPLE:-1}"
      mkShapesRDF -f "${SCRIPT_DIR}" -configs "${configs_dir}" \
        -c 1 --submit -dR 1 -l "${PILOT_EVENTS}" -q "${QUEUE}"
      ;;
    pilot)
      export LIMIT_FILES_PER_SAMPLE="${LIMIT_FILES_PER_SAMPLE:-1}"
      mkShapesRDF -f "${SCRIPT_DIR}" -configs "${configs_dir}" \
        --output-folder "${output_dir}" -c 1 -o 0 -b 0 -l "${PILOT_EVENTS}"
      ;;
    full-local)
      export LIMIT_FILES_PER_SAMPLE=-1
      mkShapesRDF -f "${SCRIPT_DIR}" -configs "${configs_dir}" \
        --output-folder "${output_dir}" -c 1 -o 0 -b 0 -l -1
      ;;
    submit)
      export LIMIT_FILES_PER_SAMPLE=-1
      export CONDOR_RUNTIME_PACKAGE=1
      mkShapesRDF -f "${SCRIPT_DIR}" -configs "${configs_dir}" \
        --output-folder "${output_dir}" -c 1 --submit -l -1 -q "${QUEUE}"
      ;;
    merge)
      mkShapesRDF -f "${SCRIPT_DIR}" -configs "${configs_dir}" \
        --output-folder "${output_dir}" -c 0 --histoadd
      ;;
  esac
}

case "${MODE}" in
  summary)
    export PAIRING_OUTPUT_ROOT="${SCRIPT_DIR}/rootFiles/${PAIRING_CAMPAIGN}"
    python "${SCRIPT_DIR}/make_summary.py" "$@"
    ;;
  plots)
    export PAIRING_OUTPUT_ROOT="${SCRIPT_DIR}/rootFiles/${PAIRING_CAMPAIGN}"
    python "${SCRIPT_DIR}/make_plots.py" "$@"
    ;;
  *)
    for era in "${ERAS[@]}"; do
      run_compile_or_analysis "${era}"
    done
    ;;
esac

echo "[Pairing] completed mode=${MODE} campaign=${PAIRING_CAMPAIGN}"
