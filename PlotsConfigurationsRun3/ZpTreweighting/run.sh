#!/usr/bin/env bash
# Activate this checkout in a child shell; the caller's environment is unchanged.
set -eo pipefail
zpt_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
zpt_start="${zpt_script_dir}/../../start.sh"
if [[ ! -f "$zpt_start" ]]; then
    echo "Framework runtime missing. Run ./install.sh from the mkShapesRDF checkout first." >&2
    exit 1
fi
source "$zpt_start"
exec python "${zpt_script_dir}/workflow.py" "$@"
