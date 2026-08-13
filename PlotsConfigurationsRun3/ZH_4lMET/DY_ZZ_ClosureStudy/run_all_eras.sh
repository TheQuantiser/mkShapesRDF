#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd)"
MODE="${1:-inspect}"
shift || true

case "${MODE}" in
  inspect|compile|pilot|submit|check|merge|summary|plots) ;;
  *)
    echo "Usage: $0 {inspect|compile|pilot|submit|check|merge|summary|plots}" >&2
    exit 2
    ;;
esac

if [[ -f "${REPO_ROOT}/start.sh" ]]; then
  set +u
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/start.sh"
fi
set -u

ERAS=(2022 2022EE 2023 2023BPix 2024)
export CLOSURE_CAMPAIGN="${CLOSURE_CAMPAIGN:-dyzz_closure_$(date -u +%Y%m%d_%H%M%S)}"
export CLOSURE_PROFILE="${CLOSURE_PROFILE:-default}"
export CLOSURE_SAMPLE_PROFILE="${CLOSURE_SAMPLE_PROFILE:-full}"
export XRD_READ_ENDPOINT="${XRD_READ_ENDPOINT:-root://eoscms.cern.ch}"
export XRD_DISCOVERY_ENDPOINT="${XRD_DISCOVERY_ENDPOINT:-${XRD_READ_ENDPOINT}}"
export FILES_PER_JOB="${FILES_PER_JOB:-10}"
QUEUE="${CLOSURE_QUEUE:-workday}"
PILOT_EVENTS="${CLOSURE_PILOT_EVENTS:-5000}"

set_year_paths() {
  local era="$1"
  export YEAR="${era}"
  export CLOSURE_CONFIGS_FOLDER="${SCRIPT_DIR}/configs/${CLOSURE_CAMPAIGN}/${era}"
  export CLOSURE_OUTPUT_FOLDER="${SCRIPT_DIR}/rootFiles/${CLOSURE_CAMPAIGN}/${era}"
  export CLOSURE_BATCH_FOLDER="${SCRIPT_DIR}/condor/${CLOSURE_CAMPAIGN}/${era}"
}

latest_pickle() {
  local directory="$1"
  local result
  result="$(find "${directory}" -maxdepth 1 -type f -name 'config_*.pkl' -printf '%T@ %p\n' | sort -n | tail -n 1 | cut -d' ' -f2-)"
  if [[ -z "${result}" ]]; then
    echo "No timestamped configuration pickle under ${directory}" >&2
    return 1
  fi
  printf '%s\n' "${result}"
}

run_era() {
  local era="$1"
  local pickle
  set_year_paths "${era}"
  echo "[DY_ZZ_ClosureStudy] mode=${MODE} campaign=${CLOSURE_CAMPAIGN} era=${era}"
  case "${MODE}" in
    inspect)
      python3 "${SCRIPT_DIR}/inspect_plan.py" --year "${era}" \
        --sample-profile "${CLOSURE_SAMPLE_PROFILE}" --closure-profile "${CLOSURE_PROFILE}" \
        --files-per-job "${FILES_PER_JOB}"
      ;;
    compile)
      export LIMIT_FILES_PER_SAMPLE="${LIMIT_FILES_PER_SAMPLE:-1}"
      mkShapesRDF -f "${SCRIPT_DIR}" -configs "${CLOSURE_CONFIGS_FOLDER}" \
        --output-folder "${CLOSURE_OUTPUT_FOLDER}" -c 1 --submit -dR 1 \
        -l "${PILOT_EVENTS}" -q "${QUEUE}"
      ;;
    pilot)
      export LIMIT_FILES_PER_SAMPLE="${LIMIT_FILES_PER_SAMPLE:-1}"
      mkShapesRDF -f "${SCRIPT_DIR}" -configs "${CLOSURE_CONFIGS_FOLDER}" \
        --output-folder "${CLOSURE_OUTPUT_FOLDER}" -c 1 -o 0 -b 0 \
        -l "${PILOT_EVENTS}"
      ;;
    submit)
      unset SAMPLE_FILTER DATA_STREAM_FILTER
      export CLOSURE_SAMPLE_PROFILE=full
      export LIMIT_FILES_PER_SAMPLE=-1
      export CONDOR_RUNTIME_PACKAGE=1
      mkShapesRDF -f "${SCRIPT_DIR}" -configs "${CLOSURE_CONFIGS_FOLDER}" \
        --output-folder "${CLOSURE_OUTPUT_FOLDER}" -c 1 --submit -l -1 -q "${QUEUE}"
      ;;
    check)
      pickle="$(latest_pickle "${CLOSURE_CONFIGS_FOLDER}")"
      mkShapesRDF -f "${SCRIPT_DIR}" -config "${pickle}" -c 0 --check -b 1
      ;;
    merge)
      pickle="$(latest_pickle "${CLOSURE_CONFIGS_FOLDER}")"
      mkShapesRDF -f "${SCRIPT_DIR}" -config "${pickle}" \
        --output-folder "${CLOSURE_OUTPUT_FOLDER}" -c 0 --histoadd -b 0
      ;;
  esac
}

case "${MODE}" in
  summary)
    inputs=()
    for era in "${ERAS[@]}"; do
      mapfile -t merged_files < <(
        find "${SCRIPT_DIR}/rootFiles/${CLOSURE_CAMPAIGN}/${era}" -maxdepth 1 \
          -type f -name 'mkShapes__*.root' ! -name '*__ALL__*' | sort
      )
      if [[ "${#merged_files[@]}" -ne 1 ]]; then
        echo "Expected exactly one merged ROOT file for ${era}, found ${#merged_files[@]}" >&2
        printf '  %s\n' "${merged_files[@]}" >&2
        exit 1
      fi
      root_file="${merged_files[0]}"
      inputs+=("${era}=${root_file}")
    done
    python3 "${SCRIPT_DIR}/make_summary.py" "${inputs[@]}" \
      --output "${SCRIPT_DIR}/summary/${CLOSURE_CAMPAIGN}"
    ;;
  plots)
    for era in 2022 2022EE 2023 2023BPix 2024 combined_2022 combined_2023 ALL_RUN3; do
      python3 "${SCRIPT_DIR}/make_plots.py" \
        --summary "${SCRIPT_DIR}/summary/${CLOSURE_CAMPAIGN}" \
        --output "${SCRIPT_DIR}/plots/${CLOSURE_CAMPAIGN}/${era}" --era "${era}"
    done
    ;;
  *)
    for era in "${ERAS[@]}"; do
      run_era "${era}"
    done
    ;;
esac

echo "[DY_ZZ_ClosureStudy] completed mode=${MODE} campaign=${CLOSURE_CAMPAIGN}"
