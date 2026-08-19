"""Validated loader for the declarative run-stability production profiles."""

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path


PROFILE_CONFIG_PATH = Path(__file__).resolve().with_name("run_stability_profiles.json")


def _number_sequence(value, *, field, size):
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"{field} must contain exactly {size} numbers")
    converted = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"{field} must contain only numbers")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError(f"{field} must contain only finite numbers")
        converted.append(number)
    return tuple(converted)


def _validate_selection_profile(name, profile):
    if not isinstance(profile, dict):
        raise ValueError(f"selection_profiles.{name} must be an object")
    for field, size in (
        ("z0_pair_pt_mins", 2),
        ("ordered_2l_pt_mins", 2),
    ):
        values = _number_sequence(
            profile.get(field), field=f"selection_profiles.{name}.{field}", size=size
        )
        if any(value < 0.0 for value in values):
            raise ValueError(
                f"selection_profiles.{name}.{field} cannot contain negative values"
            )


def _validate_axis(name, definition):
    if not isinstance(definition, dict):
        raise ValueError(f"axes.{name} must be an object")
    for field in ("expression", "label"):
        if not isinstance(definition.get(field), str) or not definition[field].strip():
            raise ValueError(f"axes.{name}.{field} must be a nonempty string")
    uniform = definition.get("uniform")
    _number_sequence(uniform, field=f"axes.{name}.uniform", size=3)
    if isinstance(uniform[0], bool) or not isinstance(uniform[0], int):
        raise ValueError(f"axes.{name}.uniform[0] must be an integer bin count")
    bins, start, stop = uniform
    if bins <= 0 or not float(start) < float(stop):
        raise ValueError(
            f"axes.{name}.uniform needs a positive bin count and increasing bounds"
        )
    fold = definition.get("fold")
    if isinstance(fold, bool) or not isinstance(fold, int) or fold not in (0, 1, 2, 3):
        raise ValueError(f"axes.{name}.fold must be one of 0, 1, 2, or 3")


def _validate_production_profile(name, profile, selections):
    if not isinstance(profile, dict):
        raise ValueError(f"production_profiles.{name} must be an object")
    for field in (
        "analysis_pass",
        "region",
        "selection_profile",
        "observable_selector",
        "luminosity_binding",
    ):
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            raise ValueError(f"production_profiles.{name}.{field} must be nonempty")
    if profile["selection_profile"] not in selections:
        raise ValueError(
            f"production_profiles.{name}.selection_profile is not configured"
        )
    category_definitions = profile.get("category_definitions")
    if not isinstance(category_definitions, dict):
        raise ValueError(
            f"production_profiles.{name}.category_definitions must be an object"
        )
    for group in ("flavors", "streams", "trigger_families", "concrete_paths"):
        records = category_definitions.get(group)
        if not isinstance(records, list) or not records:
            raise ValueError(
                f"production_profiles.{name}.category_definitions.{group} "
                "must be a nonempty list"
            )
        identifiers = []
        aggregate_ordinals = []
        for record in records:
            required = {"id", "expression", "label"}
            if group == "trigger_families":
                required = {
                    "id",
                    "aggregate",
                    "label",
                    "luminosity_source",
                    "trigmaker_family",
                }
            if group == "concrete_paths":
                required = {"id", "aggregate", "label", "luminosity_source"}
            if not isinstance(record, dict) or any(
                not isinstance(record.get(field), str) or not record[field].strip()
                for field in required
            ):
                raise ValueError(
                    f"production_profiles.{name}.category_definitions.{group} "
                    f"entries require {sorted(required)}"
                )
            identifiers.append(record["id"])
            if group == "concrete_paths" and (
                isinstance(record.get("ordinal"), bool)
                or not isinstance(record.get("ordinal"), int)
                or record["ordinal"] < 0
            ):
                raise ValueError(
                    f"production_profiles.{name}.category_definitions.{group} "
                    "entries require a nonnegative integer ordinal"
                )
            if group == "concrete_paths":
                aggregate_ordinals.append((record["aggregate"], record["ordinal"]))
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                f"production_profiles.{name}.category_definitions.{group} "
                "contains duplicate ids"
            )
        if aggregate_ordinals and len(aggregate_ordinals) != len(
            set(aggregate_ordinals)
        ):
            raise ValueError(
                f"production_profiles.{name}.category_definitions.{group} "
                "contains duplicate aggregate/ordinal joins"
            )
    for field in ("observables",):
        values = profile.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value for value in values)
            or len(values) != len(set(values))
        ):
            raise ValueError(
                f"production_profiles.{name}.{field} must be a nonempty unique list"
            )
    mass_window = _number_sequence(
        profile.get("mass_window_gev"),
        field=f"production_profiles.{name}.mass_window_gev",
        size=2,
    )
    if not mass_window[0] < mass_window[1]:
        raise ValueError(
            f"production_profiles.{name}.mass_window_gev must be increasing"
        )
    if not isinstance(profile.get("mass_window_strict"), bool):
        raise ValueError(
            f"production_profiles.{name}.mass_window_strict must be boolean"
        )
    axes = profile.get("axes")
    if not isinstance(axes, dict) or tuple(axes) != tuple(profile["observables"]):
        raise ValueError(
            f"production_profiles.{name}.axes must match observable order exactly"
        )
    for axis_name, definition in axes.items():
        _validate_axis(axis_name, definition)
    mass_axis = axes.get("Z0_mass", {}).get("uniform", ())
    if tuple(float(value) for value in mass_axis[1:]) != tuple(mass_window):
        raise ValueError(
            f"production_profiles.{name}.axes.Z0_mass bounds must equal "
            "mass_window_gev"
        )
    selected_thresholds = _number_sequence(
        selections[profile["selection_profile"]].get("ordered_2l_pt_mins"),
        field=(f"selection_profiles.{profile['selection_profile']}.ordered_2l_pt_mins"),
        size=2,
    )
    for axis_name, threshold in zip(("lZ1_pt", "lZ2_pt"), selected_thresholds):
        if (
            float(axes.get(axis_name, {}).get("uniform", [None, math.nan])[1])
            != threshold
        ):
            raise ValueError(
                f"production_profiles.{name}.axes.{axis_name} lower bound must "
                "equal its ordered_2l_pt_mins threshold"
            )
    expected_contract = profile.get("expected_category_contract")
    if (
        not isinstance(expected_contract, dict)
        or isinstance(expected_contract.get("count"), bool)
        or not isinstance(expected_contract.get("count"), int)
        or expected_contract["count"] <= 0
        or not isinstance(expected_contract.get("selector_sha256"), str)
        or len(expected_contract["selector_sha256"]) != 64
        or any(
            character not in "0123456789abcdef"
            for character in expected_contract["selector_sha256"]
        )
    ):
        raise ValueError(
            f"production_profiles.{name}.expected_category_contract is invalid"
        )


def _load_profiles():
    try:
        payload = json.loads(PROFILE_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Cannot load run-stability profiles from {PROFILE_CONFIG_PATH}: {exc}"
        ) from exc
    if payload.get("schema_version") != 1:
        raise ValueError("run_stability_profiles.json schema_version must be 1")
    default = payload.get("default_production_profile")
    profiles = payload.get("production_profiles")
    selections = payload.get("selection_profiles")
    if not isinstance(profiles, dict) or default not in profiles:
        raise ValueError("Default run-stability production profile is not configured")
    if not isinstance(selections, dict) or not selections:
        raise ValueError("run_stability_profiles.json needs selection_profiles")
    for name, profile in selections.items():
        _validate_selection_profile(name, profile)
    for name, profile in profiles.items():
        _validate_production_profile(name, profile, selections)
    return payload


RUN_STABILITY_PROFILE_CONFIG = _load_profiles()
DEFAULT_RUN_STABILITY_PRODUCTION_PROFILE = RUN_STABILITY_PROFILE_CONFIG[
    "default_production_profile"
]
SELECTION_PROFILES = deepcopy(RUN_STABILITY_PROFILE_CONFIG["selection_profiles"])
RUN_STABILITY_PRODUCTION_PROFILES = deepcopy(
    RUN_STABILITY_PROFILE_CONFIG["production_profiles"]
)


def uniform_axis_edges(definition):
    """Expand a validated ``[n_bins, start, stop]`` uniform-axis declaration."""

    uniform = definition.get("uniform")
    if (
        not isinstance(uniform, list)
        or len(uniform) != 3
        or isinstance(uniform[0], bool)
        or not isinstance(uniform[0], int)
        or uniform[0] <= 0
    ):
        raise ValueError("Uniform axes require [positive integer bins, start, stop]")
    bins, start, stop = int(uniform[0]), float(uniform[1]), float(uniform[2])
    if not start < stop:
        raise ValueError("Uniform axis start must be smaller than stop")
    width = (stop - start) / bins
    return tuple(start + width * index for index in range(bins + 1))


def run_stability_production_profile(name=None):
    """Return an isolated copy of a checked-in production profile."""

    selected = (
        str(
            name
            or os.environ.get("RUN_STABILITY_PRODUCTION_PROFILE")
            or DEFAULT_RUN_STABILITY_PRODUCTION_PROFILE
        )
        .strip()
        .lower()
    )
    if selected not in RUN_STABILITY_PRODUCTION_PROFILES:
        raise ValueError(
            f"Unknown RUN_STABILITY_PRODUCTION_PROFILE={selected!r}; "
            f"available={sorted(RUN_STABILITY_PRODUCTION_PROFILES)}"
        )
    profile = deepcopy(RUN_STABILITY_PRODUCTION_PROFILES[selected])
    profile["name"] = selected
    profile["observables"] = tuple(profile["observables"])
    profile["mass_window_gev"] = tuple(float(x) for x in profile["mass_window_gev"])
    for definition in profile["axes"].values():
        definition["uniform"] = tuple(definition["uniform"])
        definition["edges"] = uniform_axis_edges(
            {"uniform": list(definition["uniform"])}
        )
        definition["fold"] = int(definition["fold"])
    return profile


def configured_category_names(profile=None):
    """Derive the public category tuple from declarative dimensions only."""

    selected = (
        deepcopy(profile) if profile is not None else run_stability_production_profile()
    )
    definitions = selected["category_definitions"]
    flavors = tuple(record["id"] for record in definitions["flavors"])
    streams = tuple(record["id"] for record in definitions["streams"])
    families = tuple(record["id"] for record in definitions["trigger_families"])
    paths = tuple(record["id"] for record in definitions["concrete_paths"])
    split_ids = (
        ("ALL",)
        + flavors
        + streams
        + tuple(f"{stream}_{flavor}" for stream in streams for flavor in flavors)
        + families
        + paths
        + tuple(f"{family}_{flavor}" for family in families for flavor in flavors)
        + tuple(f"{path}_{flavor}" for path in paths for flavor in flavors)
    )
    names = tuple(f"DY_{split_id}" for split_id in split_ids)
    expected = selected["expected_category_contract"]
    selector_sha256 = hashlib.sha256(",".join(names).encode("utf-8")).hexdigest()
    if (
        len(names) != expected["count"]
        or selector_sha256 != expected["selector_sha256"]
    ):
        raise RuntimeError(
            "Derived RunStability category contract drifted from the checked-in "
            "JSON integrity receipt: "
            f"count={len(names)} (expected {expected['count']}), "
            f"sha256={selector_sha256} "
            f"(expected {expected['selector_sha256']})"
        )
    return names
