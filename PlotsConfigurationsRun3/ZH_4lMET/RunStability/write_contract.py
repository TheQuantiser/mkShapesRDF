"""Generate the durable compiled RunStability contract from runtime objects."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
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


def _compact_number(value):
    number = float(value)
    return (
        str(int(number))
        if number.is_integer()
        else format(number, ".12g").replace(".", "p")
    )


def _git(*args):
    completed = subprocess.run(
        ["git", *args],
        cwd=CONFIG_DIR,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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


def _validated_run_stability_tag_identity():
    advertised = globals().get("RUN_STABILITY_TAG_CONTRACT")
    if advertised is None:
        return None

    failures = []
    expected_observables = tuple(advertised["observables"])
    resolved_observables = tuple(RUN_STABILITY_CONTRACT.get("observables", ()))
    if resolved_observables != expected_observables:
        failures.append(
            f"observables={resolved_observables!r}, expected={expected_observables!r}"
        )

    resolved_categories = tuple(RUN_STABILITY_CONTRACT.get("categories", ()))
    resolved_category_selector = ",".join(resolved_categories)
    resolved_category_sha256 = hashlib.sha256(
        resolved_category_selector.encode()
    ).hexdigest()
    if resolved_categories != tuple(advertised["categories"]):
        failures.append("resolved category order differs from the advertised selector")
    if resolved_category_sha256 != advertised["category_selector_sha256"]:
        failures.append(
            "resolved category hash differs from the advertised category hash"
        )

    if RUN_STABILITY_CONTRACT.get("target_region") != advertised["region"]:
        failures.append(
            f"region={RUN_STABILITY_CONTRACT.get('target_region')!r}, "
            f"expected={advertised['region']!r}"
        )
    if SELECTED_SELECTION_PROFILE.get("name") != advertised["selection_profile"]:
        failures.append(
            "resolved selection profile differs from the advertised profile"
        )
    resolved_pt = tuple(
        float(value)
        for value in SELECTED_SELECTION_PROFILE.get("ordered_2l_pt_mins", ())
    )
    if resolved_pt != tuple(advertised["ordered_2l_pt_mins_gev"]):
        failures.append(
            f"ordered selected-Z thresholds={resolved_pt!r}, "
            f"expected={tuple(advertised['ordered_2l_pt_mins_gev'])!r}"
        )

    dy_expression = str(cuts.get("DY", {}).get("expr", ""))
    mass_bounds = re.findall(
        r"Z0_mass\s*(>=|<=|>|<)\s*([0-9]+(?:\.[0-9]*)?)", dy_expression
    )
    advertised_mass = tuple(float(value) for value in advertised["mass_window_gev"])
    configured_bounds = [
        (direction, float(value))
        for direction, value in mass_bounds
        if float(value) in advertised_mass
    ]
    expected_operators = (
        (">", "<") if advertised["mass_window_strict"] else (">=", "<=")
    )
    expected_bounds = [
        (expected_operators[0], advertised_mass[0]),
        (expected_operators[1], advertised_mass[1]),
    ]
    if configured_bounds != expected_bounds:
        failures.append(
            f"DY mass bounds={configured_bounds!r}, " f"expected={expected_bounds!r}"
        )
    if "Passes2lOrderedPt" not in dy_expression:
        failures.append("DY parent does not consume Passes2lOrderedPt")

    expected_axes = {
        name: ([float(value) for value in definition["edges"]], definition["fold"])
        for name, definition in SELECTED_RUN_STABILITY_PRODUCTION_PROFILE[
            "axes"
        ].items()
    }
    for name, (expected_edges, expected_fold) in expected_axes.items():
        definition = variables.get(name, {})
        axis = definition.get("range", ())
        resolved_edges = list(axis[0]) if len(axis) == 1 else []
        resolved_fold = int(definition.get("fold", 0))
        if resolved_edges != expected_edges or resolved_fold != expected_fold:
            failures.append(
                f"{name} axis/fold differs from declarative contract: "
                f"edges={resolved_edges!r}, fold={resolved_fold!r}"
            )

    pt_text = _compact_number(resolved_pt[0])
    if resolved_pt[1] != resolved_pt[0]:
        pt_text += "-" + _compact_number(resolved_pt[1])
    expected_tag_prefix = (
        f"DYRS_{YEAR}_pt{pt_text}_"
        f"m{_compact_number(advertised_mass[0])}to"
        f"{_compact_number(advertised_mass[1])}_"
        f"obs{len(expected_observables)}_cat{len(resolved_categories)}-"
        f"{advertised['category_selector_sha256'][:8]}_"
    )
    if not tag.startswith(expected_tag_prefix):
        failures.append(f"tag={tag!r} does not start with {expected_tag_prefix!r}")
    timestamp = str(advertised.get("timestamp_utc_compact", ""))
    if not re.fullmatch(r"[0-9]{8}T[0-9]{12}Z", timestamp):
        failures.append(f"timestamp={timestamp!r} is not compact UTC with microseconds")
    if advertised.get("tag") != tag or not tag.endswith(f"_{timestamp}"):
        failures.append("advertised tag/timestamp does not equal the compiled tag")

    if failures:
        raise RuntimeError(
            "Run-stability tag would misrepresent the resolved contract: "
            + "; ".join(failures)
        )

    validated = deepcopy(advertised)
    validated["resolved_validation"] = {
        "passed": True,
        "category_selector_sha256": resolved_category_sha256,
        "dy_parent_expression": dy_expression,
        "axis_contract": {
            name: {"edges": edges, "fold": fold}
            for name, (edges, fold) in expected_axes.items()
        },
    }
    RUN_STABILITY_TAG_CONTRACT.clear()
    RUN_STABILITY_TAG_CONTRACT.update(deepcopy(validated))
    return validated


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
        "sample_profile": SAMPLE_PROFILE,
        "sample_profile_groups": list(SAMPLE_PROFILE_GROUPS),
        "sample_profile_outputs": list(SAMPLE_PROFILE_OUTPUTS),
        "sample_selection_source": SAMPLE_SELECTION_SOURCE,
        "selection_profile": deepcopy(SELECTED_SELECTION_PROFILE),
        "nonprompt_background_included": False,
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
            {
                "aliases": aliases,
                "variables": variables,
                "cuts": cuts,
                "nuisances": nuisances,
            }
        ),
        "input_registry_sha256": _sha256(sample_contract),
    }
    if RUN_STABILITY_CONTRACT.get("enabled"):
        active_categories = tuple(CATEGORY_METADATA)
        if active_categories != tuple(RUN_STABILITY_CATEGORIES):
            raise RuntimeError(
                "RUN_STABILITY category inventory diverges from the resolved "
                f"contract: active={active_categories}, "
                f"resolved={tuple(RUN_STABILITY_CATEGORIES)}"
            )
        missing_observables = [
            name for name in RUN_STABILITY_OBSERVABLES if name not in variables
        ]
        if missing_observables:
            raise RuntimeError(
                "RUN_STABILITY requested observables are not active: "
                + ", ".join(missing_observables)
            )
        missing_pairs = {
            category: [
                observable
                for observable in RUN_STABILITY_OBSERVABLES
                if observable not in CATEGORY_VARIABLES[category]
            ]
            for category in RUN_STABILITY_CATEGORIES
        }
        missing_pairs = {
            category: observables
            for category, observables in missing_pairs.items()
            if observables
        }
        if missing_pairs:
            raise RuntimeError(
                "RUN_STABILITY requires every requested observable in every "
                f"category; missing pairs: {missing_pairs}"
            )
        contract["run_stability"] = deepcopy(RUN_STABILITY_CONTRACT)
        tag_identity = _validated_run_stability_tag_identity()
        if tag_identity is not None:
            contract["tag_identity"] = tag_identity
            contract["production_identity"] = {
                "tag": tag,
                "job_campaign": JOB_CAMPAIGN,
                "production_campaign": PRODUCTION_CAMPAIGN,
                "job_control_dir": jobControlDir,
                "output_file": outputFile,
            }
    contract["contract_sha256"] = _sha256(contract)
    return contract


def _write_contract(contract, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_jsonable(contract), indent=2, sort_keys=True) + "\n"
    )
    os.replace(temporary, destination)


analysisContract = build_analysis_contract()
analysisContractPath = os.path.abspath(
    os.path.join(configsFolder, "analysis_contract.json")
)
_write_contract(analysisContract, analysisContractPath)
_write_contract(analysisContract, os.path.join(jobControlDir, "analysis_contract.json"))
