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
TRIGGER_SPLITS = OrderedDict(
    (
        ("TRG_ELMU", ("Trigger_ElMu", "e#mu trigger family")),
        ("TRG_SINGLEMU", ("Trigger_sngMu", "single-#mu trigger family")),
        ("TRG_DOUBLEMU", ("Trigger_dblMu", "double-#mu trigger family")),
        ("TRG_SINGLEEL", ("Trigger_sngEl", "single-e trigger family")),
        ("TRG_DOUBLEEL", ("Trigger_dblEl", "double-e trigger family")),
    )
)
CATEGORY_PROFILES = ("minimal", "flavor", "stream", "trigger", "debug")


def _profile_splits(region, profile):
    base = REGION_REGISTRY[region]["splits"]
    out = OrderedDict((("ALL", base["ALL"]),))
    if profile in ("flavor", "debug"):
        out.update((key, value) for key, value in base.items() if key != "ALL")
    if profile in ("stream", "debug"):
        out.update(STREAM_SPLITS)
    if profile in ("trigger", "debug"):
        out.update(TRIGGER_SPLITS)
    return out


def build_categories(analysis_pass_name=None, profile=None):
    """Return executable cuts and metadata from one bounded registry."""
    pass_cfg = analysis_pass(analysis_pass_name)
    profile = str(
        profile
        or globals().get("CATEGORY_PROFILE")
        or os.environ.get("CATEGORY_PROFILE", "minimal")
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
        for split_id, (split_expr, split_label) in splits.items():
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
            }

    max_categories = int(os.environ.get("MAX_CATEGORIES", "30"))
    if len(metadata) > max_categories and not _env_bool("ALLOW_LARGE_PLAN"):
        raise RuntimeError(
            f"Category plan has {len(metadata)} categories, above MAX_CATEGORIES="
            f"{max_categories}; set ALLOW_LARGE_PLAN=1 for deliberate debugging"
        )
    print(
        f"ZZ_CR category plan: profile={profile}, final_categories={len(metadata)}"
    )
    return materialized, metadata, profile
