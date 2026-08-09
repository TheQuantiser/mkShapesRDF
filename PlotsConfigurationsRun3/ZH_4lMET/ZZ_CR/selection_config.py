"""Shared selection configuration for the four-lepton study."""

import os

# https://github.com/TheQuantiser/mkShapesRDF/blob/682e4abbb2cb14e9d42482d0b90723ec64520b81/mkShapesRDF/processor/data/TrigMaker_cfg.py#L1082

if "load_selected_year" not in globals():
    _candidates = [
        globals().get("CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    _config_dir = None
    for _cand in _candidates:
        if not _cand:
            continue
        _cand_abs = os.path.abspath(_cand)
        if os.path.exists(os.path.join(_cand_abs, "year_config.py")):
            _config_dir = _cand_abs
            break
    if _config_dir is None:
        _config_dir = os.path.abspath(os.getcwd())
    exec(
        open(os.path.join(_config_dir, "year_config.py")).read(),
        globals(),
        globals(),
    )

_, _selected_year, _ = load_selected_year()

ANALYSIS_PASS_CONTRACT = {
    "ALL": {
        "cuts": (
            "inclusive_z_dy",
            "four_lepton_base",
            "zz_control_region",
            "signal_region",
        ),
        # ALL loads the superset of correction aliases.  The configuration's
        # custom runner applies the expressions below per cut, because the
        # parent selections overlap and therefore cannot share one global
        # selected-object/b-tag weight.
        "selected_lepton_sf": "ZX",
        "trigger_sf": "event",
        "btag_sf": True,
        "cut_weights": {
            "inclusive_z_dy": {"*": "SelectedLeptonSF_Z"},
            "four_lepton_base": {"*": "SelectedLeptonSF_ZX"},
            "zz_control_region": {"*": "SelectedLeptonSF_ZX*BTagVetoSF"},
            "signal_region": {"*": "SelectedLeptonSF_ZX*BTagVetoSF"},
        },
        "description": "All Z/DY, four-lepton, ZZ-control, and signal regions in one nominal production",
    },
    "ZPARENT": {
        "cuts": ("inclusive_z_dy",),
        "selected_lepton_sf": "Z",
        "trigger_sf": "event",
        "btag_sf": False,
        "description": "Inclusive Z/DY baseline and diagnostic categories",
    },
    "FOURL_BASE": {
        "cuts": ("four_lepton_base",),
        "selected_lepton_sf": "ZX",
        "trigger_sf": "event",
        "btag_sf": False,
        "description": "Four-lepton preselection without a b veto",
    },
    "CONTROL": {
        "cuts": ("zz_control_region", "signal_region"),
        "selected_lepton_sf": "ZX",
        "trigger_sf": "event",
        "btag_sf": True,
        "description": "AN2019/238 ZZ control and ZH4l signal regions",
    },
}

# Stable cut/category identifiers remain suitable for ROOT directories and
# merging.  Plotting uses these independent, compact TLatex labels.
CUT_DISPLAY_LABELS = {
    "inclusive_z_dy": "Inclusive Z/DY",
    "four_lepton_base": "4#it{l} preselection",
    "zz_control_region": "ZZ control region",
    "signal_region": "ZH4#it{l} signal region",
}

CATEGORY_DISPLAY_LABELS = {
    "ALL": "Inclusive",
    "ZEE": "Z_{0}#rightarrow ee",
    "ZMM": "Z_{0}#rightarrow#mu#mu",
    "X_SF": "X_{SF}",
    "X_DF": "X_{DF}",
    "XSF": "X_{SF}",
    "XDF": "X_{DF}",
    "MuonEG_stream": "MuonEG stream",
    "Muon_stream": "Muon stream",
    "EGamma_stream": "EGamma stream",
}

def plot_category_label(cut_name, category_name):
    """Return the presentation label without changing stable identifiers."""
    if cut_name not in CUT_DISPLAY_LABELS:
        raise KeyError(f"Missing display label for cut {cut_name!r}")
    category_label = CATEGORY_DISPLAY_LABELS.get(
        category_name, category_name.replace("_", " ")
    )
    return f"{CUT_DISPLAY_LABELS[cut_name]}: {category_label}"


def analysis_pass(pass_name=None):
    """Resolve the fail-closed, disjoint execution contract."""
    name = str(
        pass_name
        or globals().get("ANALYSIS_PASS")
        or os.environ.get("ANALYSIS_PASS", "ALL")
    ).strip().upper()
    if name not in ANALYSIS_PASS_CONTRACT:
        raise ValueError(
            f"Unknown ANALYSIS_PASS={name!r}; "
            f"available={sorted(ANALYSIS_PASS_CONTRACT)}"
        )
    out = dict(ANALYSIS_PASS_CONTRACT[name])
    out["name"] = name
    out["cuts"] = tuple(out["cuts"])
    out["cut_weights"] = {
        cut_name: (
            dict(weight_policy)
            if isinstance(weight_policy, dict)
            else {"*": str(weight_policy)}
        )
        for cut_name, weight_policy in out.get("cut_weights", {}).items()
    }
    return out

_pair_cfg = _selected_year.get("lepton_ids", {})

# Pair-ID config for Z0/X lepton pairs.
PAIR_ID_CONFIG = {
    "eleWP": _pair_cfg.get("electron_wp", "cutBased_LooseID_tthMVA_Run3"),
    "muWP": _pair_cfg.get("muon_wp", "cut_TightID_pfIsoTight_HWW_tthmva_67"),
    # Required leptons passing the selected WP (0..2).
    "Z0_minPass": int(_pair_cfg.get("z0_min_pass", 2)),
    "X_minPass": int(_pair_cfg.get("x_min_pass", 2)),
    # Per-pair pT thresholds: (leading, subleading).
    "Z0_ptMins": tuple(_pair_cfg.get("z0_pt_mins", (25.0, 10.0))),
    "X_ptMins": tuple(_pair_cfg.get("x_pt_mins", (10.0, 10.0))),
}

# Shared pair indices/combinations for aliases and variables.
LEPTON_PAIR_INDEX_EXPRESSIONS = {
    "lZ1": "Alt(Z0_idx, 0, -1)",
    "lZ2": "Alt(Z0_idx, 1, -1)",
    "lX1": "Alt(X_idx, 0, -1)",
    "lX2": "Alt(X_idx, 1, -1)",
}

LEPTON_PAIR_COMBINATIONS = [
    ("lZ1", "lZ2"),
    ("lZ1", "lX1"),
    ("lZ1", "lX2"),
    ("lZ2", "lX1"),
    ("lZ2", "lX2"),
    ("lX1", "lX2"),
]

# Trigger-path config for concrete HLT branches corresponding to each aggregate
# Trigger_* flag used in samples.py/cuts.py.  These branches are persisted by
# variables.py so downstream plotting notebooks can split by actual HLT path.
TRIGGER_PATH_CONFIG = _selected_year.get("trigger_paths", {})

TRIGGER_AGGREGATE_FLAGS = [
    "Trigger_ElMu",
    "Trigger_sngMu",
    "Trigger_dblMu",
    "Trigger_sngEl",
    "Trigger_dblEl",
]

TRIGGER_PATH_PRIORITY = [
    ("HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL", "Mu23_Ele12"),
    ("HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ", "Mu12_Ele23"),
    ("HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ", "Mu8_Ele23"),
    ("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8", "Mu17_Mu8"),
    ("HLT_IsoMu24", "IsoMu24"),
    ("HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL", "Ele23_Ele12"),
    ("HLT_Ele30_WPTight_Gsf", "Ele30"),
]

TRIGGER_PATH_LABELS = dict(TRIGGER_PATH_PRIORITY)

TRIGOBJ_BASE_SUFFIXES = [
    "trigObj_idx",
    "trigObj_dR",
    "trigObj_nMatches",
    "trigObj_matchState",
    "trigObj_pt",
    "trigObj_eta",
    "trigObj_phi",
    "trigObj_pdgId",
    "trigObj_id",
    "trigObj_filterBits",
    "trigObj_bits4l",
]

TRIGOBJ_DECODED_BIT_SUFFIXES = [
    "trigObj_bit_ele_CaloIdLTrackIdLIsoVL",
    "trigObj_bit_ele_1eWPTight",
    "trigObj_bit_ele_1eWPLoose",
    "trigObj_bit_ele_DoubleEle",
    "trigObj_bit_ele_DoubleEleLeg1",
    "trigObj_bit_ele_DoubleEleLeg2",
    "trigObj_bit_ele_EleMu",
    "trigObj_bit_ele_Ele30WPTight",
    "trigObj_bit_mu_TrkIsoVVL",
    "trigObj_bit_mu_Iso",
    "trigObj_bit_mu_SingleMu",
    "trigObj_bit_mu_DoubleMu",
    "trigObj_bit_mu_EleMu",
]

TRIGOBJ_FAMILY_SUFFIXES = [
    "trigObj_match_SingleMu",
    "trigObj_match_DoubleMu",
    "trigObj_match_SingleEle",
    "trigObj_match_DoubleEle",
    "trigObj_match_EleMu",
    "trigObj_fired_SingleMu",
    "trigObj_fired_DoubleMu",
    "trigObj_fired_SingleEle",
    "trigObj_fired_DoubleEle",
    "trigObj_fired_EleMu",
]

TRIGOBJ_PATH_LEG_SUFFIXES = [
    "trigObj_leg_IsoMu24",
    "trigObj_leg_Mu17_Mu8",
    "trigObj_leg_Ele23_Ele12",
    "trigObj_leg_Ele23_Ele12_leg1",
    "trigObj_leg_Ele23_Ele12_leg2",
    "trigObj_leg_Ele30",
    "trigObj_leg_Mu23_Ele12",
    "trigObj_leg_Mu12_Ele23",
    "trigObj_leg_Mu8_Ele23",
]

TRIGOBJ_DIAGNOSTIC_SUFFIXES = (
    TRIGOBJ_BASE_SUFFIXES
    + TRIGOBJ_DECODED_BIT_SUFFIXES
    + TRIGOBJ_FAMILY_SUFFIXES
    + TRIGOBJ_PATH_LEG_SUFFIXES
)

SELECTED_LEPTON_SF_SUFFIXES = (
    "SelectedLeptonSF_Z",
    "SelectedLeptonSF_Z_Up",
    "SelectedLeptonSF_Z_Down",
    "SelectedLeptonSF_ZX",
    "SelectedLeptonSF_ZX_Up",
    "SelectedLeptonSF_ZX_Down",
    "SelectedElectronSF_Z_Up",
    "SelectedElectronSF_Z_Down",
    "SelectedMuonSF_Z_Up",
    "SelectedMuonSF_Z_Down",
    "SelectedElectronSF_ZX_Up",
    "SelectedElectronSF_ZX_Down",
    "SelectedMuonSF_ZX_Up",
    "SelectedMuonSF_ZX_Down",
)

EVENT_TRIGGER_DIAGNOSTIC_BRANCHES = [
    "dataStreamPriority",
    "triggerFamilyPriority",
    "nFiredTriggerFamilies",
    "hltPathPriority",
    "nFiredHLTPaths",
    "streamPriority_MuonEG",
    "streamPriority_Muon",
    "streamPriority_EGamma",
    "hasValidZ0",
    "hasValidX",
    "dyLike2lBaseline",
    "fourLeptonIncremental",
    "Z0_trigMatchState",
    "X_trigMatchState",
    "trigMatchState_4l",
]

DEFAULT_TRIGOBJ_NANOAOD_VERSION = 15


def trigobj_nanoaod_version(year_cfg=None):
    """Return the input-production NanoAOD trigger-object schema version."""
    cfg = year_cfg or _selected_year
    version = cfg.get("trigobj_nanoaod_version")
    if version is None:
        era = str(cfg.get("l2tight_era", ""))
        version = 12 if "v12" in era else DEFAULT_TRIGOBJ_NANOAOD_VERSION
    try:
        version = int(version)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid trigobj_nanoaod_version={version!r}; expected an integer."
        ) from exc
    if version not in (12, 15):
        raise ValueError(
            f"Unsupported trigobj_nanoaod_version={version}; expected NanoAODv12 or v15."
        )
    return version


def selection_profile(year_cfg=None, profile_name=None):
    """Resolve the named configurable four-lepton pT profile."""
    cfg = year_cfg or _selected_year
    profiles = cfg.get("selection_profiles") or cfg.get("lepton_ids", {}).get(
        "selection_profiles", {}
    )
    name = profile_name or os.environ.get("SELECTION_PROFILE", "run3_lowpt")
    if name not in profiles:
        raise ValueError(
            f"Unknown SELECTION_PROFILE={name!r}; available={sorted(profiles)}"
        )
    profile = dict(profiles[name])
    ordered = tuple(float(x) for x in profile.get("ordered_pt_mins", ()))
    if len(ordered) != 4:
        raise ValueError(f"Selection profile '{name}' needs four ordered pT thresholds")
    profile["ordered_pt_mins"] = ordered
    profile["name"] = name
    return profile


def trigger_path_branches():
    branches = []
    seen = set()
    for trigger_cfg in TRIGGER_PATH_CONFIG.values():
        for path in trigger_cfg.get("paths", []) or []:
            if path in seen:
                continue
            seen.add(path)
            branches.append(path)
    return branches


def trigger_path_entries():
    for aggregate, trigger_cfg in TRIGGER_PATH_CONFIG.items():
        for path in trigger_cfg.get("paths", []) or []:
            yield {
                "aggregate": aggregate,
                "family": trigger_cfg.get("family", ""),
                "description": trigger_cfg.get("description", ""),
                "path": path,
            }
