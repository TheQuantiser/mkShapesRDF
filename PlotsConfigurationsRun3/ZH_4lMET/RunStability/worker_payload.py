"""Materialize one worker-side analysis payload per compiled configuration."""

import os
import pickle
import zlib
from pathlib import Path


def _runtime_include(path):
    """Register one external worker resource and return its relocation token."""
    resolved = os.path.realpath(os.path.abspath(os.path.expanduser(str(path))))
    for index, existing in enumerate(condorRuntimeIncludes):
        existing_path = Path(existing).expanduser()
        if not existing_path.is_absolute():
            existing_path = Path(CONFIG_DIR) / existing_path
        if os.path.realpath(existing_path) == resolved:
            return f"__MKSHAPESRDF_RUNTIME_INCLUDE_{index:03d}__"
    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"Packaged worker resource does not exist: {resolved}")
    condorRuntimeIncludes.append(resolved)
    return f"__MKSHAPESRDF_RUNTIME_INCLUDE_{len(condorRuntimeIncludes) - 1:03d}__"


def _relocate(value, replacements):
    if isinstance(value, str):
        for source, token in replacements:
            value = value.replace(source, token)
        return value
    if isinstance(value, list):
        return [_relocate(item, replacements) for item in value]
    if isinstance(value, tuple):
        return tuple(_relocate(item, replacements) for item in value)
    if isinstance(value, dict):
        return {key: _relocate(item, replacements) for key, item in value.items()}
    return value


sharedBatchPayload = os.path.abspath(
    os.path.join(jobControlDir, "run_stability_worker_payload.pkl.zlib")
)

_payload_replacements = []

_worker_payload = {
    "aliases": aliases,
    "variables": variables,
    "cuts": {"cuts": cuts, "preselections": preselections},
    "nuisances": nuisances,
    "lumi": lumi,
    "selectionProfile": SELECTED_SELECTION_PROFILE,
    "runStabilityTagIdentity": RUN_STABILITY_TAG_CONTRACT,
    "analysisContract": analysisContract,
    "runStabilityContract": RUN_STABILITY_CONTRACT,
    "remoteIO": remoteIO,
}
_worker_payload = _relocate(_worker_payload, _payload_replacements)

if condorRuntimePackage:
    _serialized_payload = repr(_worker_payload)
    if "/afs/" in _serialized_payload:
        raise RuntimeError(
            "Packaged worker payload retains an unresolved CERN AFS dependency"
        )

_payload_path = Path(sharedBatchPayload)
_payload_path.parent.mkdir(parents=True, exist_ok=True)
_temporary_path = _payload_path.with_suffix(_payload_path.suffix + ".tmp")
with open(_temporary_path, "wb") as _payload_handle:
    _payload_handle.write(
        zlib.compress(pickle.dumps(_worker_payload, protocol=pickle.HIGHEST_PROTOCOL))
    )
os.replace(_temporary_path, _payload_path)

# Register the generated payload after atomically materializing it.  The core
# runtime packager treats explicit include files independently of its deliberate
# jobs/.pkl exclusions and rewrites sharedBatchPayload to this worker-local
# include token when producing each split script.
if condorRuntimePackage:
    _runtime_include(sharedBatchPayload)
