"""Materialize the selected-Z and trigger contracts for RunStability."""

import os

from run_stability_production import (
    SELECTION_PROFILES,
    run_stability_production_profile,
)


if "load_selected_year" not in globals():
    _config_dir = os.path.dirname(os.path.abspath(__file__))
    exec(
        open(os.path.join(_config_dir, "year_config.py")).read(),
        globals(),
        globals(),
    )

_, _selected_year, _ = load_selected_year()
_PRODUCTION_PROFILE = run_stability_production_profile()

ANALYSIS_PASS_CONTRACT = {
    _PRODUCTION_PROFILE["analysis_pass"]: {
        "cuts": ("DY",),
        "selected_lepton_sf": "Z",
        "trigger_sf": "Z",
        "description": "Inclusive selected-Z/DY run stability",
    }
}


def analysis_pass(pass_name=None):
    """Resolve the single public execution pass and reject clone-era modes."""

    name = (
        str(
            pass_name
            or globals().get("ANALYSIS_PASS")
            or os.environ.get("ANALYSIS_PASS", _PRODUCTION_PROFILE["analysis_pass"])
        )
        .strip()
        .upper()
    )
    if name not in ANALYSIS_PASS_CONTRACT:
        raise ValueError(
            f"Unknown ANALYSIS_PASS={name!r}; "
            f"available={sorted(ANALYSIS_PASS_CONTRACT)}"
        )
    resolved = dict(ANALYSIS_PASS_CONTRACT[name])
    resolved["name"] = name
    resolved["cuts"] = tuple(resolved["cuts"])
    return resolved


def selected_correction_weight(pass_contract=None):
    """Return the nominal MC correction for the selected dilepton object."""

    resolved = dict(pass_contract or analysis_pass())
    pair = resolved["selected_lepton_sf"]
    trigger = resolved["trigger_sf"]
    return f"puWeight*SelectedLeptonSF_{pair}*TriggerSF_{trigger}"


def selection_profile(profile_name=None):
    """Return the selected profile declared by the active production profile."""

    name = (
        str(
            profile_name
            or globals().get("SELECTION_PROFILE")
            or os.environ.get(
                "SELECTION_PROFILE", _PRODUCTION_PROFILE["selection_profile"]
            )
        )
        .strip()
        .lower()
    )
    if name not in SELECTION_PROFILES:
        raise ValueError(
            f"Unknown SELECTION_PROFILE={name!r}; available={sorted(SELECTION_PROFILES)}"
        )
    profile = dict(SELECTION_PROFILES[name])
    allowed = tuple(str(value).upper() for value in profile["allowed_analysis_passes"])
    active_pass = analysis_pass()["name"]
    if active_pass not in allowed:
        raise ValueError(
            f"SELECTION_PROFILE={name!r} allows {allowed}; received {active_pass!r}"
        )
    if str(profile["target_region"]).upper() != _PRODUCTION_PROFILE["region"]:
        raise ValueError(
            f"SELECTION_PROFILE={name!r} targets {profile['target_region']!r}, "
            f"not {_PRODUCTION_PROFILE['region']!r}"
        )
    for field in ("z0_pair_pt_mins", "ordered_2l_pt_mins"):
        values = tuple(float(value) for value in profile[field])
        if len(values) != 2:
            raise ValueError(f"SELECTION_PROFILE={name!r} needs two values in {field}")
        profile[field] = values
    profile["name"] = name
    return profile


SELECTED_SELECTION_PROFILE = selection_profile()
SELECTION_PROFILE = SELECTED_SELECTION_PROFILE["name"]

_pair_cfg = _selected_year["lepton_ids"]
PAIR_ID_CONFIG = {
    "eleWP": _pair_cfg["electron_wp"],
    "muWP": _pair_cfg["muon_wp"],
    "Z0_minPass": int(_pair_cfg["z0_min_pass"]),
    "Z0_ptMins": tuple(SELECTED_SELECTION_PROFILE["z0_pair_pt_mins"]),
}

_TRIGGER_FAMILY_DEFINITIONS = tuple(
    _PRODUCTION_PROFILE["category_definitions"]["trigger_families"]
)
TRIGGER_AGGREGATE_FLAGS = tuple(
    record["aggregate"] for record in _TRIGGER_FAMILY_DEFINITIONS
)
TRIGMAKER_TRIGGER_FAMILIES = {
    record["aggregate"]: record["trigmaker_family"]
    for record in _TRIGGER_FAMILY_DEFINITIONS
}


def canonical_trigmaker_paths(year_cfg=None):
    """Return the ordered DATA/MC HLT union for the configured TrigMaker era."""

    from mkShapesRDF.processor.data.TrigMaker_cfg import Trigger

    cfg = year_cfg or _selected_year
    era = cfg["l2tight_era"]
    if era not in Trigger:
        raise RuntimeError(f"Configured TrigMaker era {era!r} does not exist")
    by_mode = {}
    for mode in ("DATA", "MC"):
        resolved = {aggregate: [] for aggregate in TRIGMAKER_TRIGGER_FAMILIES}
        for period in Trigger[era].values():
            mode_cfg = period.get(mode, {})
            for aggregate, family in TRIGMAKER_TRIGGER_FAMILIES.items():
                for path in mode_cfg.get(family, ()):
                    if path not in resolved[aggregate]:
                        resolved[aggregate].append(path)
        by_mode[mode] = {
            aggregate: tuple(paths) for aggregate, paths in resolved.items()
        }
    if by_mode["DATA"] != by_mode["MC"]:
        raise RuntimeError(
            f"TrigMaker era {era!r} has different DATA and MC HLT path sets"
        )
    return by_mode["DATA"]


def validate_trigger_path_config(year_cfg=None):
    """Reject any configured concrete-path inventory that differs from TrigMaker."""

    cfg = year_cfg or _selected_year
    expected = canonical_trigmaker_paths(cfg)
    configured = {
        aggregate: tuple(cfg["trigger_paths"][aggregate]["paths"])
        for aggregate in TRIGMAKER_TRIGGER_FAMILIES
    }
    if configured != expected:
        differences = []
        for aggregate in TRIGMAKER_TRIGGER_FAMILIES:
            missing = tuple(
                path
                for path in expected[aggregate]
                if path not in configured[aggregate]
            )
            extra = tuple(
                path
                for path in configured[aggregate]
                if path not in expected[aggregate]
            )
            if missing or extra:
                differences.append(
                    f"{aggregate}: missing={missing or ()}, extra={extra or ()}"
                )
        raise RuntimeError(
            f"YEAR={cfg['year']} trigger_paths disagree with TrigMaker era "
            f"{cfg['l2tight_era']!r}: " + "; ".join(differences)
        )
    return True


validate_trigger_path_config(_selected_year)

# Category IDs and labels are profile-owned. Physical HLT branches are
# year-owned. The aggregate+ordinal join below is validated to cover every
# configured path exactly once, so neither Python nor the profile repeats a
# physical trigger path.
_CONCRETE_PATH_DEFINITIONS = tuple(
    _PRODUCTION_PROFILE["category_definitions"]["concrete_paths"]
)
_configured_paths = _selected_year["trigger_paths"]
_materialized_paths = []
for record in _CONCRETE_PATH_DEFINITIONS:
    aggregate = record["aggregate"]
    ordinal = record["ordinal"]
    if aggregate not in _configured_paths:
        raise ValueError(
            f"Concrete-path category {record['id']!r} uses unknown aggregate "
            f"{aggregate!r}"
        )
    paths = tuple(_configured_paths[aggregate]["paths"])
    if ordinal >= len(paths):
        raise ValueError(
            f"Concrete-path category {record['id']!r} ordinal {ordinal} is "
            f"outside {aggregate} paths {paths}"
        )
    materialized = dict(record)
    materialized["path"] = paths[ordinal]
    _materialized_paths.append(materialized)

_all_configured_paths = tuple(
    path
    for aggregate in TRIGGER_AGGREGATE_FLAGS
    for path in _configured_paths[aggregate]["paths"]
)
_materialized_physical_paths = tuple(record["path"] for record in _materialized_paths)
if len(_materialized_physical_paths) != len(set(_materialized_physical_paths)) or set(
    _materialized_physical_paths
) != set(_all_configured_paths):
    raise ValueError(
        "Configured concrete-path category definitions must cover the exact "
        "year_config.json HLT path inventory exactly once"
    )
TRIGGER_PATH_DEFINITIONS = tuple(_materialized_paths)
TRIGGER_PATH_PRIORITY = tuple(
    (record["path"], record["label"]) for record in TRIGGER_PATH_DEFINITIONS
)

TRIGGER_PATH_LABELS = dict(TRIGGER_PATH_PRIORITY)
