"""Materialize the JSON-declared DY run-stability category contract."""

from collections import OrderedDict

from run_stability_production import (
    configured_category_names as declared_category_names,
    run_stability_production_profile,
)

if "TRIGGER_PATH_DEFINITIONS" not in globals():
    from selection_config import (
        TRIGGER_AGGREGATE_FLAGS,
        TRIGGER_PATH_DEFINITIONS,
        analysis_pass,
    )


_PROFILE = run_stability_production_profile()
_DEFINITIONS = _PROFILE["category_definitions"]

TRIGGER_OR = "(" + " || ".join(TRIGGER_AGGREGATE_FLAGS) + ")"
PRESELECTION = f"{TRIGGER_OR} && nLepton >= 2 && L2TightLeading2 && nJetInHorn == 0"

# Z0_idx already owns the profile-defined pair-construction thresholds. The
# active ordered 35/35 GeV analysis threshold is applied exactly once through
# Passes2lOrderedPt in RUN_STABILITY_DY_PARENT below.
SELECTED_Z_QUALITY = "hasValidZ0"

_MASS_MIN, _MASS_MAX = _PROFILE["mass_window_gev"]
_MASS_OPERATORS = (">", "<") if _PROFILE["mass_window_strict"] else (">=", "<=")
RUN_STABILITY_DY_PARENT = (
    f"{SELECTED_Z_QUALITY} && Z0_mass {_MASS_OPERATORS[0]} {_MASS_MIN:g}. "
    f"&& Z0_mass {_MASS_OPERATORS[1]} {_MASS_MAX:g}. && Passes2lOrderedPt"
)


def _records(name):
    records = _DEFINITIONS.get(name)
    if not isinstance(records, list) or not records:
        raise ValueError(f"category_definitions.{name} must be a nonempty list")
    out = OrderedDict()
    for record in records:
        category_id = str(record.get("id", ""))
        expression = str(record.get("expression", record.get("aggregate", "")))
        label = str(record.get("label", ""))
        if not category_id or not expression or not label or category_id in out:
            raise ValueError(f"Invalid or duplicate category_definitions.{name} entry")
        out[category_id] = (expression, label, dict(record))
    return out


FLAVORS = _records("flavors")
STREAMS = _records("streams")
TRIGGER_FAMILIES = _records("trigger_families")

RUN_STABILITY_TRIGGER_FAMILY_SOURCES = OrderedDict(
    (
        category_id,
        (record[2]["luminosity_source"], record[2]["aggregate"]),
    )
    for category_id, record in TRIGGER_FAMILIES.items()
)


HLT_PATHS = OrderedDict(
    (
        record["id"],
        (
            record["path"],
            record["label"],
            {
                "luminosity_source": record["luminosity_source"],
                "scope_name": record["path"],
            },
        ),
    )
    for record in TRIGGER_PATH_DEFINITIONS
)
RUN_STABILITY_HLT_PATH_SOURCES = OrderedDict(
    (category_id, (record[2]["luminosity_source"], record[2]["scope_name"]))
    for category_id, record in HLT_PATHS.items()
)


def _split_record(
    expression,
    label,
    view_type,
    partition_family,
    exclusive,
    luminosity_source="trigger_any",
):
    return {
        "expr": expression,
        "label": label,
        "view_type": view_type,
        "partition_family": partition_family,
        "is_exclusive_within_family": bool(exclusive),
        "is_overlapping_projection": not bool(exclusive),
        "run_stability_luminosity_source": luminosity_source,
    }


def _add_base_splits(splits):
    splits["ALL"] = _split_record("1", "Inclusive", "inclusive", "DY:inclusive", False)
    for category_id, (expression, label, _) in FLAVORS.items():
        splits[category_id] = _split_record(
            expression, label, "flavor", "DY:selected_z_flavor", True
        )


def _add_stream_splits(splits):
    for category_id, (expression, label, _) in STREAMS.items():
        splits[category_id] = _split_record(
            expression, label, "stream", "DY:data_stream_priority", True
        )
    for stream_id, (stream_expr, stream_label, _) in STREAMS.items():
        for flavor_id, (flavor_expr, flavor_label, _) in FLAVORS.items():
            splits[f"{stream_id}_{flavor_id}"] = _split_record(
                f"({stream_expr}) && ({flavor_expr})",
                f"{stream_label}, {flavor_label}",
                "stream_flavor",
                "DY:data_stream_priority_x_selected_z_flavor",
                True,
            )


def _add_trigger_splits(splits, records, sources, view_type, family):
    for category_id, (expression, label, _) in records.items():
        source = sources[category_id][0]
        splits[category_id] = _split_record(
            expression, label, view_type, family, False, source
        )


def _add_trigger_flavor_splits(splits, records, sources, view_type, family):
    for category_id, (expression, label, _) in records.items():
        source = sources[category_id][0]
        for flavor_id, (flavor_expr, flavor_label, _) in FLAVORS.items():
            splits[f"{category_id}_{flavor_id}"] = _split_record(
                f"({expression}) && ({flavor_expr})",
                f"{label}, {flavor_label}",
                view_type,
                f"{family}_x_selected_z_flavor",
                False,
                source,
            )


def _configured_splits():
    splits = OrderedDict()
    _add_base_splits(splits)
    _add_stream_splits(splits)
    _add_trigger_splits(
        splits,
        TRIGGER_FAMILIES,
        RUN_STABILITY_TRIGGER_FAMILY_SOURCES,
        "trigger",
        "DY:positive_trigger_family",
    )
    _add_trigger_splits(
        splits,
        HLT_PATHS,
        RUN_STABILITY_HLT_PATH_SOURCES,
        "trigger_path",
        "DY:concrete_hlt_path",
    )
    _add_trigger_flavor_splits(
        splits,
        TRIGGER_FAMILIES,
        RUN_STABILITY_TRIGGER_FAMILY_SOURCES,
        "trigger",
        "DY:positive_trigger_family",
    )
    _add_trigger_flavor_splits(
        splits,
        HLT_PATHS,
        RUN_STABILITY_HLT_PATH_SOURCES,
        "trigger_path",
        "DY:concrete_hlt_path",
    )
    return splits


def configured_category_names():
    """Validate executable splits against the declarative public order."""

    names = tuple(f"DY_{split_id}" for split_id in _configured_splits())
    declared = declared_category_names(_PROFILE)
    if names != declared:
        raise RuntimeError(
            "Executable category materialization differs from the declarative "
            "RunStability category order"
        )
    return declared


def build_categories(analysis_pass_name=None, profile=None):
    """Return the sole supported DY cut and its ordered category metadata."""

    pass_cfg = analysis_pass(analysis_pass_name)
    if pass_cfg["name"] != _PROFILE["analysis_pass"]:
        raise ValueError(
            f"RunStability supports only ANALYSIS_PASS={_PROFILE['analysis_pass']}"
        )
    selected_profile = str(profile or "standard").strip().lower()
    if selected_profile != "standard":
        raise ValueError("RunStability supports only CATEGORY_PROFILE=standard")

    splits = _configured_splits()
    materialized = OrderedDict(
        (
            (
                "DY",
                {
                    "expr": RUN_STABILITY_DY_PARENT,
                    "categories": OrderedDict(
                        (split_id, definition["expr"])
                        for split_id, definition in splits.items()
                    ),
                    "weights": {"*": "1.f"},
                },
            ),
        )
    )
    metadata = OrderedDict()
    for split_id, split in splits.items():
        category_id = f"DY_{split_id}"
        metadata[category_id] = {
            "category_id": category_id,
            "display_label": f"Inclusive Z/DY: {split['label']}",
            "physics_region": "DY",
            "parent_expression": RUN_STABILITY_DY_PARENT,
            "split_expression": split["expr"],
            "full_cut_expression": (
                f"({PRESELECTION}) && ({RUN_STABILITY_DY_PARENT}) "
                f"&& ({split['expr']})"
            ),
            "weight_policy": "1.f",
            "weight_domain": "selected-Z leptons and selected-Z trigger algebra",
            "category_weight_factor": "1.f",
            "data_weight_rule": (
                "METFilter_DATA with DATA trigger-stream de-duplication; "
                "no MC scale factors"
            ),
            "recommended_variable_groups": ["dy", "trigger", "weights"],
            "category_profile": selected_profile,
            **split,
        }
    return materialized, metadata, selected_profile
