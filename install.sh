#!/usr/bin/env bash
set -eo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${repo_root}"

mode="default"
check_only=0
force_dependencies=0
skip_dependencies=0
for argument in "$@"; do
    case "${argument}" in
        docker) mode="docker" ;;
        --check) check_only=1 ;;
        --force-dependencies) force_dependencies=1 ;;
        --skip-dependencies) skip_dependencies=1 ;;
        -h|--help)
            printf '%s\n' \
                "usage: ./install.sh [docker] [--check] [--force-dependencies|--skip-dependencies]" \
                "" \
                "--check validates the existing runtime without changing it." \
                "--force-dependencies reruns network-capable pip installation." \
                "--skip-dependencies uses an already prepared system/LCG Python stack."
            exit 0
            ;;
        *)
            printf 'Unsupported install option: %s\n' "${argument}" >&2
            exit 64
            ;;
    esac
done
if [[ ${force_dependencies} -eq 1 && ${skip_dependencies} -eq 1 ]]; then
    printf '%s\n' '--force-dependencies and --skip-dependencies are mutually exclusive' >&2
    exit 64
fi

fail_line() {
    printf 'install.sh failed at line %s; review the command above and prerequisites in docs/condor_remote_io.rst\n' "$1" >&2
}
trap 'fail_line "$LINENO"' ERR

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        printf 'Required command is unavailable: %s\n' "$1" >&2
        return 1
    fi
}

architecture="$(uname -m)"
if [[ "${architecture}" != "x86_64" ]]; then
    printf 'Unsupported default architecture: %s (supported: x86_64; provide a compatible prepared runtime explicitly)\n' "${architecture}" >&2
    exit 1
fi

runtime_setup=""
if [[ "${mode}" == "docker" ]]; then
    require_command root-config
else
    os_cpe="$(sed -n 's/^CPE_NAME=//p' /etc/os-release | tr -d '"')"
    if [[ -n "${MKSHAPESRDF_LCG_VIEW:-}" ]]; then
        runtime_setup="${MKSHAPESRDF_LCG_VIEW%/}/setup.sh"
    elif [[ "${os_cpe}" == *"centos:7"* ]]; then
        runtime_setup="/cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-centos7-gcc11-opt/setup.sh"
    elif [[ "${os_cpe}" == *"linux:9"* ]]; then
        runtime_setup="/cvmfs/sft.cern.ch/lcg/views/LCG_109/x86_64-el9-gcc13-opt/setup.sh"
    else
        printf 'Unsupported default OS runtime: %s; set MKSHAPESRDF_LCG_VIEW to a compatible LCG view\n' "${os_cpe}" >&2
        exit 1
    fi
    if [[ ! -r "${runtime_setup}" ]]; then
        printf 'LCG runtime setup is not readable: %s\n' "${runtime_setup}" >&2
        exit 1
    fi
    # LCG setup scripts are not guaranteed to tolerate nounset in callers.
    source "${runtime_setup}"
fi

python_command="python"
if ! command -v "${python_command}" >/dev/null 2>&1; then
    python_command="python3"
fi
require_command "${python_command}"
require_command root-config
require_command c++
require_command sha256sum

validate_existing_runtime() {
    local expected="${repo_root}/mkShapesRDF/__init__.py"
    for required in myenv/bin/python start.sh utils/bin/hadd2; do
        if [[ ! -e "${repo_root}/${required}" ]]; then
            printf 'Installed runtime member is missing: %s\n' "${repo_root}/${required}" >&2
            return 1
        fi
    done
    (
        cd /tmp
        source "${repo_root}/start.sh"
        python - "${expected}" <<'PY'
from pathlib import Path
import mkShapesRDF
import sys

expected = Path(sys.argv[1]).resolve()
resolved = Path(mkShapesRDF.__file__).resolve()
print(f"python={sys.executable}")
print(f"mkShapesRDF={resolved}")
if resolved != expected:
    raise SystemExit(f"wrong mkShapesRDF checkout: expected {expected}, got {resolved}")
PY
    )
}

if [[ ${check_only} -eq 1 ]]; then
    validate_existing_runtime
    printf 'Existing mkShapesRDF runtime is valid for %s on %s\n' "${repo_root}" "${architecture}"
    exit 0
fi

if [[ ! -x myenv/bin/python ]]; then
    "${python_command}" -m venv --system-site-packages myenv
fi
source myenv/bin/activate
local_python_path="$(python - <<'PY'
import site
print(site.getsitepackages()[0])
PY
)"
if [[ "${local_python_path}" != "${repo_root}/"* ]]; then
    printf 'Virtual-environment site-packages escaped the checkout: %s\n' "${local_python_path}" >&2
    exit 1
fi
local_python_relative="${local_python_path#${repo_root}/}"

dependency_fingerprint="$({
    printf '%s\n' "${repo_root}"
    sha256sum pyproject.toml setup.cfg
} | sha256sum | awk '{print $1}')"
dependency_marker="myenv/.mkshapesrdf_dependency_fingerprint"
installed_fingerprint=""
if [[ -r "${dependency_marker}" ]]; then
    installed_fingerprint="$(<"${dependency_marker}")"
fi

if [[ ${skip_dependencies} -eq 1 ]]; then
    printf '%s\n' 'Skipping pip installation by explicit request; system/LCG dependencies must already be complete.'
elif [[ ${force_dependencies} -eq 1 || "${dependency_fingerprint}" != "${installed_fingerprint}" ]]; then
    python -m pip install -e ".[docs,dev,processor]"
    # A system-site-packages venv can retain stale local Sphinx dist-info when
    # pip selects an immutable LCG Sphinx as the uninstall target.  Reinstall
    # the documented constraint explicitly so both imports and dependency
    # metadata converge for upgraded existing checkouts as well as fresh ones.
    python -m pip uninstall -y sphinx
    python -m pip install --force-reinstall --no-deps "sphinx>=8.2,<9"
    python - "${local_python_path}" <<'PY'
from pathlib import Path
import email
import shutil
import sys

from packaging.specifiers import SpecifierSet

site_packages = Path(sys.argv[1]).resolve()
constraint = SpecifierSet(">=8.2,<9")
for metadata_dir in site_packages.glob("sphinx-*.dist-info"):
    metadata_file = metadata_dir / "METADATA"
    if not metadata_file.is_file():
        continue
    metadata = email.message_from_string(metadata_file.read_text())
    if metadata.get("Name", "").lower() != "sphinx":
        continue
    version = metadata.get("Version", "")
    if version not in constraint:
        print(f"Removing incompatible local Sphinx metadata: {metadata_dir.name}")
        shutil.rmtree(metadata_dir)
PY
    python -m pip install --no-binary=correctionlib correctionlib
    printf '%s\n' "${dependency_fingerprint}" >"${dependency_marker}"
else
    printf '%s\n' 'Dependency metadata and checkout path are unchanged; skipping pip installation.'
fi

mkdir -p utils/bin
if [[ ! -x utils/bin/hadd2 || utils/src/hadd.cxx -nt utils/bin/hadd2 ]]; then
    c++ utils/src/hadd.cxx -o utils/bin/hadd2.part $(root-config --cflags --libs)
    mv utils/bin/hadd2.part utils/bin/hadd2
    chmod 0755 utils/bin/hadd2
fi

jsonpog_destination="mkShapesRDF/processor/data/jsonpog-integration/POG"
if [[ ! -d "${jsonpog_destination}" ]]; then
    jsonpog_source="/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG"
    if [[ ! -d "${jsonpog_source}" ]]; then
        printf 'Required CMS JSON POG source is unavailable: %s\n' "${jsonpog_source}" >&2
        exit 1
    fi
    mkdir -p "$(dirname "${jsonpog_destination}")"
    cp -r "${jsonpog_source}" "$(dirname "${jsonpog_destination}")/"
fi

if [[ "${mode}" == "docker" ]]; then
    start_runtime_line='export LD_LIBRARY_PATH="$(root-config --libdir):${_mkshapes_repo}/xrdfs_locallib/lib:/.singularity.d/libs:${LD_LIBRARY_PATH:-}"'
else
    start_runtime_line="source ${runtime_setup}"
fi

cat >start.sh <<EOF
#!/usr/bin/env bash
_mkshapes_repo="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
${start_runtime_line}
source "\${_mkshapes_repo}/myenv/bin/activate"
export STARTPATH="\${_mkshapes_repo}/start.sh"
export PYTHONPATH="\${_mkshapes_repo}:\${_mkshapes_repo}/${local_python_relative}:\${PYTHONPATH:-}"
export PATH="\${_mkshapes_repo}/utils/bin:\${PATH:-}"
unset _mkshapes_repo
EOF
chmod 0755 start.sh

validate_existing_runtime
printf 'mkShapesRDF runtime is ready at %s\n' "${repo_root}"
