"""Immutable histogram registry metadata and sparse activation profiles."""

from copy import deepcopy
import hashlib
import json
import os


COMMON_ANALYSIS = (
    "Z0_mass", "Z0_pt", "Z0_eta", "Z0_phi",
    "PuppiMET_pt", "nLepton", "nCleanJet", "HT", "nPV", "nvtx", "rho",
    "dataStreamPriority", "triggerFamilyPriority", "hltPathPriority",
    "nFiredTriggerFamilies", "nFiredHLTPaths", "TriggerSF_event", "puWeight",
)
DY_ANALYSIS = COMMON_ANALYSIS + (
    "lZ1_pt", "lZ2_pt", "lZ1_eta", "lZ2_eta",
    "SelectedLeptonSF_Z", "Z0_isEE", "Z0_isMM",
)
FOURL_ANALYSIS = COMMON_ANALYSIS + (
    "X_mass", "X_pt", "X_eta", "X_phi", "m4l", "pT4l",
    "lZ1_pt", "lZ2_pt", "lX1_pt", "lX2_pt",
    "lZ1_eta", "lZ2_eta", "lX1_eta", "lX2_eta",
    "sumLeptonCharge", "X_isSF", "X_isDF", "physicalBtagVeto",
    "BTagVetoSF", "SelectedLeptonSF_ZX", "dPhi_MET_Z", "dPhi_MET_X",
    "dPhi_MET_ZplusX", "dR_lZ1_lZ2", "dR_lX1_lX2",
    "recoil_ut", "recoil_upar", "recoil_uperp",
    "CleanJet_pt_0", "CleanJet_eta_0", "CleanJet_pt_1", "CleanJet_eta_1",
)

# Analysis activation is a policy over physics meaning, not category names.
# Inclusive projections preserve the original 25/50-observable sets; cheaper
# diagnostic views retain only the observables needed for their stated use.
DY_FLAVOR = (
    "Z0_mass", "Z0_pt", "Z0_eta", "Z0_phi", "PuppiMET_pt",
    "lZ1_pt", "lZ2_pt", "lZ1_eta", "lZ2_eta", "nPV", "rho",
    "dataStreamPriority", "triggerFamilyPriority", "hltPathPriority",
    "nFiredTriggerFamilies", "nFiredHLTPaths", "TriggerSF_event",
    "SelectedLeptonSF_Z", "puWeight",
)
DY_STREAM = (
    "Z0_mass", "Z0_pt", "PuppiMET_pt",
    "lZ1_pt", "lZ2_pt", "lZ1_eta", "lZ2_eta", "nPV", "rho",
    "dataStreamPriority", "triggerFamilyPriority", "hltPathPriority",
    "nFiredTriggerFamilies", "nFiredHLTPaths", "TriggerSF_event",
    "SelectedLeptonSF_Z", "puWeight",
)
DY_STREAM_FLAVOR = (
    "Z0_mass", "Z0_pt", "PuppiMET_pt",
    "lZ1_pt", "lZ2_pt", "lZ1_eta", "lZ2_eta", "nPV", "rho",
    "dataStreamPriority", "triggerFamilyPriority", "hltPathPriority",
    "TriggerSF_event", "SelectedLeptonSF_Z", "puWeight",
)
FOURL_FLAVOR = (
    "Z0_mass", "X_mass", "m4l", "pT4l", "PuppiMET_pt", "Z0_pt", "X_pt",
    "lZ1_pt", "lZ2_pt", "lX1_pt", "lX2_pt",
    "lZ1_eta", "lZ2_eta", "lX1_eta", "lX2_eta",
    "nCleanJet", "HT", "physicalBtagVeto",
    "CleanJet_pt_0", "CleanJet_eta_0", "CleanJet_pt_1", "CleanJet_eta_1",
    "dataStreamPriority", "triggerFamilyPriority", "hltPathPriority",
    "nFiredTriggerFamilies", "nFiredHLTPaths", "TriggerSF_event",
    "SelectedLeptonSF_ZX", "BTagVetoSF", "puWeight",
)
FOURL_STREAM = (
    "Z0_mass", "X_mass", "m4l", "Z0_pt", "X_pt", "PuppiMET_pt",
    "lZ1_pt", "lZ2_pt", "lX1_pt", "lX2_pt",
    "lZ1_eta", "lZ2_eta", "lX1_eta", "lX2_eta", "nPV", "rho",
    "dataStreamPriority", "triggerFamilyPriority", "hltPathPriority",
    "nFiredTriggerFamilies", "nFiredHLTPaths", "TriggerSF_event",
    "SelectedLeptonSF_ZX", "BTagVetoSF", "puWeight",
)
FOURL_STREAM_FLAVOR = (
    "Z0_mass", "X_mass", "m4l", "PuppiMET_pt",
    "lZ1_pt", "lZ2_pt", "lX1_pt", "lX2_pt",
    "dataStreamPriority", "triggerFamilyPriority", "hltPathPriority",
    "TriggerSF_event", "SelectedLeptonSF_ZX", "BTagVetoSF", "puWeight",
)

VIEW_VARIABLE_POLICIES = {
    ("DY", "inclusive"): DY_ANALYSIS,
    ("DY", "flavor"): DY_FLAVOR,
    ("DY", "stream"): DY_STREAM,
    ("DY", "stream_flavor"): DY_STREAM_FLAVOR,
    ("DY", "trigger"): DY_STREAM,
    ("FOURL", "inclusive"): FOURL_ANALYSIS,
    ("FOURL", "flavor"): FOURL_FLAVOR,
    ("FOURL", "stream"): FOURL_STREAM,
    ("FOURL", "stream_flavor"): FOURL_STREAM_FLAVOR,
    ("FOURL", "trigger"): FOURL_STREAM,
    ("ZZCR", "inclusive"): FOURL_ANALYSIS,
    ("ZZCR", "flavor"): FOURL_FLAVOR,
    ("ZZCR", "stream"): FOURL_STREAM,
    ("ZZCR", "stream_flavor"): FOURL_STREAM_FLAVOR,
    ("ZZCR", "trigger"): FOURL_STREAM,
    ("SR", "inclusive"): FOURL_ANALYSIS,
    ("SR", "flavor"): FOURL_FLAVOR,
    ("SR", "stream"): FOURL_STREAM,
    ("SR", "stream_flavor"): FOURL_STREAM_FLAVOR,
    ("SR", "trigger"): FOURL_STREAM,
}

PROFILE_NAMES = ("analysis", "trigger", "objects", "weights", "quality", "all")


def _csv_env(name):
    return tuple(item.strip() for item in os.environ.get(name, "").split(",") if item.strip())


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _definition_hash(definition):
    immutable = {
        key: definition[key]
        for key in ("name", "range", "xaxis", "fold")
        if key in definition
    }
    return hashlib.sha256(_canonical(immutable).encode()).hexdigest()


def _tags(name):
    tags = {"analysis"} if name in set(DY_ANALYSIS) | set(FOURL_ANALYSIS) else set()
    if (
        "trig" in name.lower()
        or name.startswith("HLT_")
        or name.startswith("Trigger")
        or name in ("dataStreamPriority", "nFiredHLTPaths", "nFiredTriggerFamilies")
    ):
        tags.add("trigger")
    if name.startswith(("lZ", "lX", "CleanJet_")):
        tags.add("objects")
    if any(token in name for token in ("SF", "Weight", "Eff")):
        tags.add("weights")
    if any(
        name.endswith("_" + suffix)
        for suffix in (
            "convVeto", "dxy", "dz", "eInvMinusPInv", "hoe", "jetPtRelv2",
            "jetRelIso", "lostHits", "mvaIso_WP90", "pfIsoId",
            "pfRelIso03_all", "promptMVA", "sieie", "sip3d", "tightId",
        )
    ) or "isTight" in name:
        tags.add("quality")
    return sorted(tags or {"debug"})


def _recommended_regions(name):
    if name in DY_ANALYSIS and name not in FOURL_ANALYSIS:
        return ["DY"]
    if name in FOURL_ANALYSIS and name not in DY_ANALYSIS:
        return ["FOURL", "ZZCR", "SR"]
    if name.startswith("lX") or "ZX" in name or name.startswith("X_"):
        return ["FOURL", "ZZCR", "SR"]
    return ["DY", "FOURL", "ZZCR", "SR"]


def build_registry(raw_variables, binning_contract):
    """Decorate complete definitions without mutating their immutable fields."""
    registry = {}
    for name, raw in raw_variables.items():
        definition = deepcopy(raw)
        definition["tags"] = _tags(name)
        definition["physics_role"] = (
            "default analysis observable" if "analysis" in definition["tags"]
            else "opt-in diagnostic observable"
        )
        definition["recommended_regions"] = _recommended_regions(name)
        definition["binning_contract"] = deepcopy(binning_contract.get(name, {}))
        definition["definition_sha256"] = _definition_hash(definition)
        registry[name] = definition
    return registry


def materialize_histograms(raw_variables, binning_contract, category_metadata, profile=None):
    """Resolve active definitions and exact category-variable pairs."""
    registry = build_registry(raw_variables, binning_contract)
    profile = str(profile or os.environ.get("HISTOGRAM_PROFILE", "analysis")).lower()
    if profile not in PROFILE_NAMES:
        raise ValueError(f"Unknown HISTOGRAM_PROFILE={profile!r}; available={PROFILE_NAMES}")

    include = _csv_env("VARIABLE_INCLUDE")
    exclude = set(_csv_env("VARIABLE_EXCLUDE"))
    unknown = (set(include) | exclude) - set(registry)
    if unknown:
        raise ValueError(f"Unknown VARIABLE_INCLUDE/EXCLUDE names: {sorted(unknown)}")

    if include:
        selected = list(dict.fromkeys(include))
    elif profile == "all":
        selected = list(registry)
    else:
        selected = [
            name
            for name, definition in registry.items()
            if "analysis" in definition["tags"] or profile in definition["tags"]
        ]
    selected = [name for name in selected if name not in exclude]

    policy_names = {
        category_id: set(
            VIEW_VARIABLE_POLICIES[
                (category["physics_region"], category["view_type"])
            ]
        )
        for category_id, category in category_metadata.items()
    }
    category_variables = {category_id: [] for category_id in category_metadata}
    active = {}
    for name in selected:
        definition = deepcopy(registry[name])
        allowed = [
            category_id
            for category_id, category in category_metadata.items()
            if category["physics_region"] in definition["recommended_regions"]
            and (
                bool(include)
                or profile == "all"
                or name in policy_names[category_id]
                or (profile != "analysis" and profile in definition["tags"])
            )
        ]
        if not allowed:
            continue
        definition["categories"] = allowed
        active[name] = definition
        for category_id in allowed:
            category_variables[category_id].append(name)

    category_profile = next(iter(category_metadata.values()))["category_profile"]
    profile_action_budgets = {
        "minimal": 200,
        "standard": 1000,
        "flavor": 700,
        "stream": 500,
        "trigger": 700,
        "detailed": 1200,
        "debug": 1200,
    }
    max_actions = int(
        os.environ.get(
            "MAX_HISTOGRAM_ACTIONS", profile_action_budgets[category_profile]
        )
    )
    action_count = sum(map(len, category_variables.values()))
    allow_large = os.environ.get("ALLOW_LARGE_PLAN", "0").lower() in (
        "1", "true", "yes", "on"
    )
    if action_count > max_actions and not allow_large:
        raise RuntimeError(
            f"Histogram plan has {action_count} actions, above "
            f"MAX_HISTOGRAM_ACTIONS={max_actions}; set ALLOW_LARGE_PLAN=1 for "
            "deliberate detailed production"
        )
    for category_id, names in category_variables.items():
        if not names:
            raise RuntimeError(f"Category {category_id} has no active variables")
    print(
        f"ZZ_CR histogram plan: profile={profile}, registry={len(registry)}, "
        f"active={len(active)}, category_variable_actions={action_count}"
    )
    return registry, active, category_variables, profile
