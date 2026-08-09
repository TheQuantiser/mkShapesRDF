"""Generate the durable compiled ZZ_CR analysis contract from runtime objects."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess


def _jsonable(value):
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if callable(value):
        return getattr(value, "__name__", repr(value))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _canonical(value):
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"))


def _sha256(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _git(*args):
    completed = subprocess.run(
        ["git", *args], cwd=CONFIG_DIR, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _sample_contract():
    out = {}
    for sample_name, sample in samples.items():
        components = []
        for component in sample.get("name", []):
            components.append(
                {
                    "source": component[0],
                    "input_file_count": len(component[1]),
                    "component_weight": component[2] if len(component) > 2 else "1.0",
                    "input_registry_sha256": _sha256(component[1]),
                }
            )
        out[sample_name] = {
            "is_data": bool(sample.get("isData")),
            "sample_base_weight": sample.get("weight", "1.0"),
            "files_per_job": sample.get("FilesPerJob"),
            "components": components,
        }
    return out


def build_analysis_contract():
    sample_contract = _sample_contract()
    category_contract = {}
    for category_id, category in CATEGORY_METADATA.items():
        entry = deepcopy(category)
        names = list(CATEGORY_VARIABLES[category_id])
        entry.update(
            {
                "year": YEAR,
                "analysis_profile": ANALYSIS_PASS,
                "category_profile": CATEGORY_PROFILE,
                "histogram_profile": HISTOGRAM_PROFILE,
                "active_variables": names,
                "active_binning": {
                    name: {
                        "range": deepcopy(variables[name]["range"]),
                        "fold": variables[name].get("fold", 0),
                    }
                    for name in names
                },
                "active_nuisances": list(nuisances),
            }
        )
        category_contract[category_id] = entry

    git_sha = _git("rev-parse", "HEAD")
    dirty = bool(_git("status", "--short"))
    contract = {
        "schema_version": 1,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": git_sha,
        "git_dirty": dirty,
        "year": YEAR,
        "analysis_pass": ANALYSIS_PASS,
        "site_profile": SITE_PRESET,
        "execution_profile": SELECTED_EXECUTION_PROFILE,
        "input_access_mode": remoteIO["inputAccessMode"],
        "read_endpoint": xrdReadEndpoint,
        "write_endpoint": xrdWriteEndpoint,
        "output_mode": OUTPUT_MODE,
        "category_profile": CATEGORY_PROFILE,
        "histogram_profile": HISTOGRAM_PROFILE,
        "active_samples": sample_contract,
        "preselection": preselections,
        "categories": category_contract,
        "variables": {
            name: {
                "expression": definition["name"],
                "range": deepcopy(definition["range"]),
                "fold": definition.get("fold", 0),
                "title": definition.get("xaxis", ""),
                "categories": list(definition.get("categories", [])),
                "definition_sha256": definition["definition_sha256"],
            }
            for name, definition in variables.items()
        },
        "nuisance_mapping": _jsonable(nuisances),
        "sample_overlap_stitching_summary": _jsonable(
            globals().get("_resolved_overlap", {})
        ),
        "registry_sha256": _sha256(VARIABLE_REGISTRY_HASHES),
        "runtime_payload_sha256": _sha256(
            {"aliases": aliases, "variables": variables, "cuts": cuts, "nuisances": nuisances}
        ),
        "input_registry_sha256": _sha256(sample_contract),
    }
    contract["contract_sha256"] = _sha256(contract)
    return contract


def _write_contract(contract, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(_jsonable(contract), indent=2, sort_keys=True) + "\n")
    os.replace(temporary, destination)


analysisContract = build_analysis_contract()
analysisContractPath = os.path.abspath(os.path.join(configsFolder, "analysis_contract.json"))
_write_contract(analysisContract, analysisContractPath)
_write_contract(analysisContract, os.path.join(jobControlDir, "analysis_contract.json"))
