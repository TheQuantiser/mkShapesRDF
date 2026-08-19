"""Activate only the observables declared by the RunStability JSON profile."""

from copy import deepcopy
import hashlib
import json

from run_stability_production import run_stability_production_profile


_PROFILE = run_stability_production_profile()
DY_ANALYSIS = tuple(_PROFILE["observables"])
RUN_STABILITY_OBSERVABLE_SELECTORS = {
    _PROFILE["observable_selector"]: DY_ANALYSIS,
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _definition_hash(definition):
    immutable = {
        key: definition[key]
        for key in ("name", "range", "xaxis", "fold")
        if key in definition
    }
    return hashlib.sha256(_canonical(immutable).encode()).hexdigest()


def build_registry(raw_variables, binning_contract):
    """Decorate the complete variable definitions without changing axes."""

    registry = {}
    for name, raw in raw_variables.items():
        definition = deepcopy(raw)
        definition["tags"] = ["analysis"] if name in DY_ANALYSIS else ["inactive"]
        definition["physics_role"] = (
            "configured run-stability observable"
            if name in DY_ANALYSIS
            else "inactive inherited diagnostic"
        )
        definition["recommended_regions"] = ["DY"]
        definition["binning_contract"] = deepcopy(binning_contract.get(name, {}))
        definition["definition_sha256"] = _definition_hash(definition)
        registry[name] = definition
    return registry


def materialize_histograms(
    raw_variables,
    binning_contract,
    category_metadata,
    profile=None,
    required_category_variables=(),
    exact_required_category_variables=False,
):
    """Resolve the exact JSON-declared category-observable matrix."""

    selected_profile = str(profile or "analysis").strip().lower()
    if selected_profile != "analysis":
        raise ValueError("RunStability supports only HISTOGRAM_PROFILE=analysis")
    required = tuple(str(name) for name in required_category_variables)
    if not exact_required_category_variables or required != DY_ANALYSIS:
        raise ValueError(
            "RunStability requires the exact observable tuple from "
            "run_stability_profiles.json"
        )
    registry = build_registry(raw_variables, binning_contract)
    missing = [name for name in required if name not in registry]
    if missing:
        raise ValueError(
            f"Configured observables are absent from variables.py: {missing}"
        )
    if any(
        metadata.get("physics_region") != "DY"
        for metadata in category_metadata.values()
    ):
        raise ValueError("RunStability category metadata must be DY-only")

    active = {}
    categories = list(category_metadata)
    category_variables = {category: list(required) for category in categories}
    for name in required:
        definition = deepcopy(registry[name])
        definition["categories"] = categories
        active[name] = definition
    return registry, active, category_variables, selected_profile
