"""Declarative physics-category registry for compact ZZ_CR production."""

from collections import OrderedDict
import os

from selection_config import PAIR_ID_CONFIG, analysis_pass


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return bool(default)
    normalized = value.strip().lower()
    if normalized in ("1", "true", "yes", "on"):
        return True
    if normalized in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{name} must be boolean; received {value!r}")


TRIGGER_OR = (
    "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || "
    "Trigger_sngEl || Trigger_dblEl)"
)
PRESELECTION = (
    f"{TRIGGER_OR} && nLepton >= 2 && L2TightLeading2 && nJetInHorn == 0"
)

Z1_PT = "Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f)"
Z2_PT = "Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f)"
X1_PT = "Alt(Lepton_pt, Alt(X_idx, 0, -1), -999.f)"
X2_PT = "Alt(Lepton_pt, Alt(X_idx, 1, -1), -999.f)"
Z1_PT_MIN, Z2_PT_MIN = PAIR_ID_CONFIG["Z0_ptMins"]
X1_PT_MIN, X2_PT_MIN = PAIR_ID_CONFIG["X_ptMins"]

DY_PARENT = (
    f"{TRIGGER_OR} && nLepton >= 2 && hasValidZ0 && Z0_mass > 30."
    f" && {Z1_PT} > {Z1_PT_MIN:g} && {Z2_PT} > {Z2_PT_MIN:g}"
)
FOURL_PARENT = (
    f"{DY_PARENT} && nLepton >= 4 && hasValidX && selectedIndicesDistinct"
    f" && X_mass > 4. && {X1_PT} > {X1_PT_MIN:g}"
    f" && {X2_PT} > {X2_PT_MIN:g} && m4l > 0. && sumLeptonCharge == 0"
)
PHYSICAL_COMMON = (
    f"{FOURL_PARENT} && fifthLeptonVeto && Z0_mass > 12."
    " && physicalBtagVeto && abs(Z0_mass - 91.1876) < 15."
    " && Passes4lOrderedPt"
)
ZZCR_PARENT = (
    f"{PHYSICAL_COMMON} && X_isSF"
    " && X_mass > 75. && X_mass < 105. && PuppiMET_pt < 35."
)
SR_XSF = (
    "X_isSF && X_mass > 10. && X_mass < 65."
    " && PuppiMET_pt > 35. && m4l > 140."
)
SR_XDF = "X_isDF && X_mass > 10. && X_mass < 70. && PuppiMET_pt > 20."
SR_PARENT = f"{PHYSICAL_COMMON} && (({SR_XSF}) || ({SR_XDF}))"


REGION_REGISTRY = OrderedDict(
    (
        (
            "DY",
            {
                "display_label": "Inclusive Z/DY",
                "parent_expr": DY_PARENT,
                "weight_policy": "SelectedLeptonSF_Z",
                "weight_domain": "selected-Z leptons",
                "recommended_variable_groups": ["dy", "trigger", "weights"],
                "splits": OrderedDict(
                    (
                        ("ALL", ("1", "Inclusive")),
                        ("ZEE", ("Z0_isEE", "Z_{0}#rightarrow ee")),
                        ("ZMM", ("Z0_isMM", "Z_{0}#rightarrow#mu#mu")),
                    )
                ),
            },
        ),
        (
            "FOURL",
            {
                "display_label": "Four-lepton diagnostic parent",
                "parent_expr": FOURL_PARENT,
                "weight_policy": "SelectedLeptonSF_ZX",
                "weight_domain": "selected-ZX leptons",
                "recommended_variable_groups": ["fourl", "trigger", "weights"],
                "splits": OrderedDict((("ALL", ("1", "Inclusive")),)),
            },
        ),
        (
            "ZZCR",
            {
                "display_label": "ZZ control region",
                "parent_expr": ZZCR_PARENT,
                "weight_policy": "SelectedLeptonSF_ZX*BTagVetoSF",
                "weight_domain": "selected-ZX leptons and fixed-WP b veto",
                "recommended_variable_groups": ["fourl", "trigger", "weights"],
                "splits": OrderedDict(
                    (
                        ("ALL", ("1", "Inclusive")),
                        ("4E", ("Z0_isEE && X_isEE", "4e")),
                        ("4MU", ("Z0_isMM && X_isMM", "4#mu")),
                        (
                            "2E2MU",
                            (
                                "((Z0_isEE && X_isMM) || (Z0_isMM && X_isEE))",
                                "2e2#mu",
                            ),
                        ),
                    )
                ),
            },
        ),
        (
            "SR",
            {
                "display_label": "ZH four-lepton signal-reference region",
                "parent_expr": SR_PARENT,
                "weight_policy": "SelectedLeptonSF_ZX*BTagVetoSF",
                "weight_domain": "selected-ZX leptons and fixed-WP b veto",
                "recommended_variable_groups": ["fourl", "trigger", "weights"],
                "splits": OrderedDict(
                    (
                        ("ALL", ("1", "Inclusive")),
                        ("XSF", ("X_isSF", "X_{SF}")),
                        ("XDF", ("X_isDF", "X_{DF}")),
                    )
                ),
            },
        ),
    )
)

STREAM_SPLITS = OrderedDict(
    (
        ("STREAM_MUONEG", ("streamPriority_MuonEG", "MuonEG stream")),
        ("STREAM_MUON", ("streamPriority_Muon", "Muon stream")),
        ("STREAM_EGAMMA", ("streamPriority_EGamma", "EGamma stream")),
    )
)

# Unlike the raw Trigger_* flags, these categories are an exclusive priority
# partition.  This prevents multi-trigger events from being counted in more
# than one member of the trigger diagnostic family.
TRIGGER_PRIORITY_SPLITS = OrderedDict(
    (
        ("TRGPRIO_ELMU", ("triggerFamilyPriority == 1", "e#mu priority")),
        ("TRGPRIO_SINGLEMU", ("triggerFamilyPriority == 2", "single-#mu priority")),
        ("TRGPRIO_DOUBLEMU", ("triggerFamilyPriority == 3", "double-#mu priority")),
        ("TRGPRIO_SINGLEEL", ("triggerFamilyPriority == 4", "single-e priority")),
        ("TRGPRIO_DOUBLEEL", ("triggerFamilyPriority == 5", "double-e priority")),
    )
)

SR_TOPOLOGY_SPLITS = OrderedDict(
    (
        ("4E", ("Z0_isEE && X_isEE", "4e")),
        ("4MU", ("Z0_isMM && X_isMM", "4#mu")),
        (
            "2E2MU",
            (
                "((Z0_isEE && X_isMM) || (Z0_isMM && X_isEE))",
                "2e2#mu",
            ),
        ),
        ("3E1MU", ("Z0_isEE && X_isDF", "3e1#mu")),
        ("1E3MU", ("Z0_isMM && X_isDF", "1e3#mu")),
    )
)

DY_STREAM_FLAVOR_SPLITS = OrderedDict(
    (
        (f"{stream_id}_{flavor_id}", (f"({stream_expr}) && ({flavor_expr})", f"{stream_label}, {flavor_label}"))
        for stream_id, (stream_expr, stream_label) in STREAM_SPLITS.items()
        for flavor_id, (flavor_expr, flavor_label) in list(REGION_REGISTRY["DY"]["splits"].items())[1:]
    )
)

# These five leaves test concrete ZZ stream-closure failure modes.  Pure 4e
# and 4mu select the expected primary stream; all three priority streams are
# retained for the mixed topology.  The other four possible 3x3 leaves are
# deliberately absent.
ZZCR_STREAM_TOPOLOGY_SPLITS = OrderedDict(
    (
        ("STREAM_EGAMMA_4E", ("streamPriority_EGamma && Z0_isEE && X_isEE", "EGamma stream, 4e")),
        ("STREAM_MUON_4MU", ("streamPriority_Muon && Z0_isMM && X_isMM", "Muon stream, 4#mu")),
        ("STREAM_MUONEG_2E2MU", ("streamPriority_MuonEG && ((Z0_isEE && X_isMM) || (Z0_isMM && X_isEE))", "MuonEG stream, 2e2#mu")),
        ("STREAM_MUON_2E2MU", ("streamPriority_Muon && ((Z0_isEE && X_isMM) || (Z0_isMM && X_isEE))", "Muon stream, 2e2#mu")),
        ("STREAM_EGAMMA_2E2MU", ("streamPriority_EGamma && ((Z0_isEE && X_isMM) || (Z0_isMM && X_isEE))", "EGamma stream, 2e2#mu")),
    )
)

SR_STREAM_X_SPLITS = OrderedDict(
    (
        (f"{stream_id}_{x_id}", (f"({stream_expr}) && ({x_expr})", f"{stream_label}, {x_label}"))
        for stream_id, (stream_expr, stream_label) in STREAM_SPLITS.items()
        for x_id, (x_expr, x_label) in list(REGION_REGISTRY["SR"]["splits"].items())[1:]
    )
)

CATEGORY_PROFILES = (
    "minimal", "standard", "flavor", "stream", "trigger", "detailed", "debug"
)


def _split_record(split_expr, split_label, view_type, partition_family,
                  exclusive, overlapping, purpose):
    return {
        "expr": split_expr,
        "label": split_label,
        "view_type": view_type,
        "partition_family": partition_family,
        "is_exclusive_within_family": bool(exclusive),
        "is_overlapping_projection": bool(overlapping),
        "diagnostic_purpose": purpose,
    }


def _add_family(out, splits, view_type, partition_family, exclusive, purpose):
    for split_id, (expr, label) in splits.items():
        if split_id in out:
            continue
        out[split_id] = _split_record(
            expr, label, view_type, partition_family, exclusive, True, purpose
        )


def _profile_splits(region, profile):
    base = REGION_REGISTRY[region]["splits"]
    out = OrderedDict(
        (
            (
                "ALL",
                _split_record(
                    base["ALL"][0], base["ALL"][1], "inclusive",
                    f"{region}:inclusive", False, True,
                    "Reference projection for the complete physics region",
                ),
            ),
        )
    )

    use_flavor = profile in ("standard", "flavor", "detailed", "debug")
    use_stream = profile in ("standard", "stream", "detailed", "debug")
    if use_flavor:
        if region == "SR":
            _add_family(
                out, OrderedDict(list(base.items())[1:]), "flavor",
                "SR:selected_x_flavor", True,
                "Separate same- and different-flavor selected X pairs",
            )
            _add_family(
                out, SR_TOPOLOGY_SPLITS, "flavor", "SR:selected_4l_topology",
                True, "Exclusive selected-Z0/X four-lepton topology partition",
            )
        else:
            _add_family(
                out, OrderedDict(list(base.items())[1:]), "flavor",
                f"{region}:selected_flavor_topology", True,
                "Selected-pair flavor/topology closure",
            )
    if use_stream:
        _add_family(
            out, STREAM_SPLITS, "stream", f"{region}:data_stream_priority",
            True, "Exclusive DATA-stream-priority acceptance closure",
        )
    if profile in ("standard", "detailed", "debug"):
        if region == "DY":
            _add_family(
                out, DY_STREAM_FLAVOR_SPLITS, "stream_flavor",
                "DY:data_stream_priority_x_selected_z_flavor", True,
                "DY trigger/dataset-stream closure within selected Z flavor",
            )
        elif region == "ZZCR":
            _add_family(
                out, ZZCR_STREAM_TOPOLOGY_SPLITS, "stream_flavor",
                "ZZCR:curated_stream_x_topology", True,
                "Curated expected-stream and mixed-topology closure check",
            )
    if profile in ("detailed", "debug") and region == "SR":
        _add_family(
            out, SR_STREAM_X_SPLITS, "stream_flavor",
            "SR:data_stream_priority_x_selected_x_flavor", True,
            "Detailed stream acceptance comparison for XSF and XDF signal branches",
        )
    if profile in ("trigger", "debug"):
        _add_family(
            out, TRIGGER_PRIORITY_SPLITS, "trigger",
            f"{region}:trigger_family_priority", True,
            "Exclusive trigger-family-priority acceptance diagnostic",
        )
    return out


def build_categories(analysis_pass_name=None, profile=None):
    """Return executable cuts and metadata from one bounded registry."""
    pass_cfg = analysis_pass(analysis_pass_name)
    profile = str(
        profile
        or globals().get("CATEGORY_PROFILE")
        or os.environ.get("CATEGORY_PROFILE", "standard")
    ).strip().lower()
    if profile not in CATEGORY_PROFILES:
        raise ValueError(
            f"Unknown CATEGORY_PROFILE={profile!r}; available={CATEGORY_PROFILES}"
        )

    materialized = OrderedDict()
    metadata = OrderedDict()
    seen = set()
    for region in pass_cfg["cuts"]:
        if region not in REGION_REGISTRY:
            raise RuntimeError(f"Unknown region {region!r} in analysis pass")
        registry = REGION_REGISTRY[region]
        splits = _profile_splits(region, profile)
        runner_factor = registry["weight_policy"] if pass_cfg["name"] == "ALL" else "1.f"
        sample_base_weight = "lumi*XSWeight*METFilter_Common*puWeight*TriggerSF_event"
        if pass_cfg["name"] != "ALL":
            sample_base_weight += f"*({registry['weight_policy']})"
        materialized[region] = {
            "expr": registry["parent_expr"],
            "categories": OrderedDict(),
            "weights": {"*": runner_factor},
        }
        for split_id, split in splits.items():
            split_expr = split["expr"]
            split_label = split["label"]
            category_id = f"{region}_{split_id}"
            if category_id in seen:
                raise RuntimeError(f"Duplicate final category {category_id!r}")
            seen.add(category_id)
            if region == "ZZCR" and split_id == "XDF":
                raise RuntimeError("Impossible XDF category generated for physical ZZCR")
            materialized[region]["categories"][split_id] = split_expr
            full_cut = f"({PRESELECTION}) && ({registry['parent_expr']}) && ({split_expr})"
            category_factor = runner_factor
            metadata[category_id] = {
                "category_id": category_id,
                "display_label": f"{registry['display_label']}: {split_label}",
                "physics_region": region,
                "parent_expression": registry["parent_expr"],
                "split_expression": split_expr,
                "full_cut_expression": full_cut,
                "weight_policy": category_factor,
                "weight_domain": registry["weight_domain"],
                "sample_base_mc_weight": sample_base_weight,
                "category_weight_factor": category_factor,
                "full_nominal_mc_weight": (
                    f"{sample_base_weight}*({category_factor})"
                ),
                "data_weight_rule": "METFilter_DATA with DATA trigger-stream de-duplication; no MC scale factors",
                "recommended_variable_groups": list(
                    registry["recommended_variable_groups"]
                ),
                "category_profile": profile,
                "view_type": split["view_type"],
                "partition_family": split["partition_family"],
                "is_exclusive_within_family": split["is_exclusive_within_family"],
                "is_overlapping_projection": split["is_overlapping_projection"],
                "diagnostic_purpose": split["diagnostic_purpose"],
            }

    profile_category_budgets = {
        "minimal": 6,
        "standard": 40,
        "flavor": 20,
        "stream": 15,
        "trigger": 20,
        "detailed": 50,
        # The curated debug union deliberately crosses the ordinary limit and
        # therefore requires ALLOW_LARGE_PLAN=1.
        "debug": 50,
    }
    max_categories = int(
        os.environ.get("MAX_CATEGORIES", profile_category_budgets[profile])
    )
    if len(metadata) > max_categories and not _env_bool("ALLOW_LARGE_PLAN"):
        raise RuntimeError(
            f"Category plan has {len(metadata)} categories, above MAX_CATEGORIES="
            f"{max_categories}; set ALLOW_LARGE_PLAN=1 for deliberate debugging"
        )
    print(
        f"ZZ_CR category plan: profile={profile}, final_categories={len(metadata)}"
    )
    return materialized, metadata, profile
