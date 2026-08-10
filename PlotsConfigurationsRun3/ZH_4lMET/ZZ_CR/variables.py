import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP
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

if (
    "PAIR_ID_CONFIG" not in globals()
    or "LEPTON_PAIR_INDEX_EXPRESSIONS" not in globals()
    or "LEPTON_PAIR_COMBINATIONS" not in globals()
    or "trigger_path_branches" not in globals()
    or "TRIGOBJ_DIAGNOSTIC_SUFFIXES" not in globals()
    or "analysis_pass" not in globals()
):
    from selection_config import (
        EVENT_TRIGGER_DIAGNOSTIC_BRANCHES,
        LEPTON_PAIR_COMBINATIONS,
        LEPTON_PAIR_INDEX_EXPRESSIONS,
        PAIR_ID_CONFIG,
        TRIGGER_AGGREGATE_FLAGS,
        TRIGGER_PATH_LABELS,
        TRIGOBJ_DIAGNOSTIC_SUFFIXES,
        analysis_pass,
        trigger_path_branches,
    )

variables = {}

_VARIABLE_PASS = analysis_pass(
    globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS")
)

BASE_EVENT_BRANCHES = [

    *TRIGGER_AGGREGATE_FLAGS,

    "nCleanJet",
    "Z0_mass",
    "Z0_pt",
    "Z0_eta",
    "Z0_phi",
    "X_mass",
    "X_pt",
    "X_eta",
    "X_phi",
    "m4l",
    "pT4l",
    "phi4l",
    "PuppiMET_pt",
    "PuppiMET_phi",
    "PuppiMET_significance",
    "PuppiMET_sumEt",
    "HT",
    "nJetInHorn",
    "dPhi_MET_Z",
    "dPhi_MET_X",
    "dPhi_MET_lZ1",
    "dPhi_MET_lZ2",
    "dPhi_MET_lX1",
    "dPhi_MET_lX2",
    "dPhi_MET_ZplusX",
]

# BASE_EVENT_BRANCHES += [f"dPhi_{lep_a}_{lep_b}" for lep_a, lep_b in LEPTON_PAIR_COMBINATIONS]
# BASE_EVENT_BRANCHES += [f"dEta_{lep_a}_{lep_b}" for lep_a, lep_b in LEPTON_PAIR_COMBINATIONS]
# BASE_EVENT_BRANCHES += [f"dR_{lep_a}_{lep_b}" for lep_a, lep_b in LEPTON_PAIR_COMBINATIONS]
BASE_EVENT_BRANCHES += [
    f"{metric}_{lep_a}_{lep_b}"
    for metric in ("dPhi", "dEta", "dR")
    for lep_a, lep_b in LEPTON_PAIR_COMBINATIONS
]

BASE_EVENT_BRANCHES += [
    "recoil_ux",
    "recoil_uy",
    "recoil_ut",
    "recoil_upar",
    "recoil_uperp",
    "sumLeptonCharge",
    "Z0_isEE",
    "Z0_isMM",
    "X_isEE",
    "X_isMM",
    "X_isSF",
    "X_isDF",
    "GenMET_pt",
    "GenMET_phi",
    "bVeto",
    "Passes4lOrderedPt",
    "Passes4lOrderedPtRun2",
    "Passes4lOrderedPtRun3",
    "L2TightLeading2",
    "L2TightLeading2Naive",
    "L2TightProductionGate",
    "L2TightGateIndex0",
    "L2TightGateIndex1",
    "selectedIndicesDistinct",
    "selectedIndicesAreLeading2",
    "selectedIndicesAreLeading4",
    "TriggerSF_Z",
    "TriggerSF_Z_Up",
    "TriggerSF_Z_Down",
    "TriggerSF_ZX",
    "TriggerSF_ZX_Up",
    "TriggerSF_ZX_Down",
    "TriggerSF_Z_Valid",
    "TriggerSF_ZX_Valid",
    "TriggerEff_Z",
    "TriggerEff_ZX",
    "TriggerEffData_Z",
    "TriggerEffMC_Z",
    "TriggerEffData_ZX",
    "TriggerEffMC_ZX",
    "TriggerEffData_event",
    "TriggerEffMC_event",
    "TriggerSF_event",
    "TriggerSF_event_Up",
    "TriggerSF_event_Down",
    "TriggerSF_event_Valid",
    "TriggerEffData_selected",
    "TriggerEffMC_selected",
    "TriggerSF_selected",
    "TriggerSF_selected_Up",
    "TriggerSF_selected_Down",
    "TriggerSF_selected_Valid",
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
]

BASE_EVENT_BRANCHES += [
    f"{lep_name}_LeptonSF" for lep_name in LEPTON_PAIR_INDEX_EXPRESSIONS
]
diagnostic_expressions = {branch: branch for branch in BASE_EVENT_BRANCHES}

pair_leptons = list(LEPTON_PAIR_INDEX_EXPRESSIONS.items())

AVAILABLE_BRANCHES = globals().get("AVAILABLE_BRANCHES")


def _has_branch(branch):
    return not AVAILABLE_BRANCHES or branch in AVAILABLE_BRANCHES


def _existing_branch(branch):
    return branch if _has_branch(branch) else None


# Persist configured concrete HLT paths.  When a branch inventory is supplied, missing
# paths become false booleans instead of invalid self-definitions.
for trigger_path_branch in trigger_path_branches():
    diagnostic_expressions[trigger_path_branch] = (
        trigger_path_branch if _has_branch(trigger_path_branch) else "false"
    )

for event_diag_branch in EVENT_TRIGGER_DIAGNOSTIC_BRANCHES:
    diagnostic_expressions[event_diag_branch] = event_diag_branch

LEPTON_BRANCH_RECIPES = {
    "pt": "Lepton_pt",
    "eta": "Lepton_eta",
    "phi": "Lepton_phi",
    "pdgId": "Lepton_pdgId",
    "charge": "(Lepton_pdgId < 0) - (Lepton_pdgId > 0)",
    "genPdgId": "Lepton_genPdgId",
    "genPt": "Lepton_genPt",
    "genEta": "Lepton_genEta",
    "genPhi": "Lepton_genPhi",
}

_, _selected_year, _ = load_selected_year()
_L2TIGHT_ERA = _selected_year["l2tight_era"]
electron_tight_wps = list(
    globals().get("ELECTRON_TIGHT_WPS")
    or ElectronWP[_L2TIGHT_ERA]["TightObjWP"].keys()
)
muon_tight_wps = list(
    globals().get("MUON_TIGHT_WPS") or MuonWP[_L2TIGHT_ERA]["TightObjWP"].keys()
)

TIGHT_OBJECT_CONFIG = {
    "Electron": {
        "pdg_id": 11,
        "wps": electron_tight_wps,
        "flag_branch": "Lepton_isTightElectron",
    },
    "Muon": {
        "pdg_id": 13,
        "wps": muon_tight_wps,
        "flag_branch": "Lepton_isTightMuon",
    },
}


# LeptonMaker builds a pt-sorted merged Lepton collection and records
# Lepton_electronIdx / Lepton_muonIdx as back-references to the original
# Electron/Muon collections; pair indices (lZ1/lZ2/lX1/lX2) index this merged
# Lepton list, so quality observables must be dereferenced through those maps.
_quality_nanoaod_v15 = int(_selected_year["trigobj_nanoaod_version"]) >= 15

LEPTON_QUALITY_BRANCH_MAP = {
    "convVeto": {"ele": "Electron_convVeto", "mu": None, "default": "0"},
    "dxy": {"ele": "Electron_dxy", "mu": "Muon_dxy", "default": "-999.f"},
    "dz": {"ele": "Electron_dz", "mu": "Muon_dz", "default": "-999.f"},
    "eInvMinusPInv": {"ele": "Electron_eInvMinusPInv", "mu": None, "default": "-999.f"},
    "hoe": {"ele": "Electron_hoe", "mu": None, "default": "-999.f"},
    "jetPtRelv2": {"ele": "Electron_jetPtRelv2", "mu": "Muon_jetPtRelv2", "default": "-999.f"},
    "jetRelIso": {"ele": "Electron_jetRelIso", "mu": "Muon_jetRelIso", "default": "-999.f"},
    "lostHits": {"ele": "Electron_lostHits", "mu": None, "default": "-999"},
    "mvaIso_WP90": {"ele": "Electron_mvaIso_WP90", "mu": None, "default": "0"},
    "pfIsoId": {"ele": None, "mu": "Muon_pfIsoId", "default": "0"},
    "pfRelIso03_all": {"ele": "Electron_pfRelIso03_all", "mu": "Muon_pfRelIso03_all", "default": "-999.f"},
    "promptMVA": {
        "ele": "Electron_promptMVA" if _quality_nanoaod_v15 else None,
        "mu": "Muon_promptMVA" if _quality_nanoaod_v15 else None,
        "default": "-999.f",
    },
    "sieie": {"ele": "Electron_sieie", "mu": None, "default": "-999.f"},
    "sip3d": {"ele": "Electron_sip3d", "mu": "Muon_sip3d", "default": "-999.f"},
    "tightId": {"ele": None, "mu": "Muon_tightId", "default": "0"},
}

for lep_label, lep_idx in pair_leptons:
    for suffix, source in LEPTON_BRANCH_RECIPES.items():
        if suffix == "charge" and _has_branch("Lepton_pdgId"):
            # ``charge`` is a vector expression, not a NanoAOD branch name.
            # Checking the complete expression against AVAILABLE_BRANCHES
            # incorrectly replaces every selected-lepton charge with -999 when
            # a concrete branch inventory is supplied.
            diagnostic_expressions[f"{lep_label}_{suffix}"] = (
                f"Alt({source}, {lep_idx}, -999)"
            )
        elif _existing_branch(source):
            diagnostic_expressions[f"{lep_label}_{suffix}"] = f"Alt({source}, {lep_idx}, -999)"
        else:
            diagnostic_expressions[f"{lep_label}_{suffix}"] = "-999"


    lep_pdgid_expr = f"abs(Alt(Lepton_pdgId, {lep_idx}, 0))"
    lep_ele_idx_expr = f"Alt(Lepton_electronIdx, {lep_idx}, -1)"
    lep_mu_idx_expr = f"Alt(Lepton_muonIdx, {lep_idx}, -1)"
    for suffix, cfg in LEPTON_QUALITY_BRANCH_MAP.items():
        ele_src = cfg["ele"]
        mu_src = cfg["mu"]
        default = cfg["default"]
        ele_expr = (
            f"Alt({ele_src}, {lep_ele_idx_expr}, {default})"
            if ele_src and _has_branch(ele_src)
            else default
        )
        mu_expr = (
            f"Alt({mu_src}, {lep_mu_idx_expr}, {default})"
            if mu_src and _has_branch(mu_src)
            else default
        )
        diagnostic_expressions[f"{lep_label}_{suffix}"] = (
            f"({lep_pdgid_expr} == 11) ? ({ele_expr}) : (({lep_pdgid_expr} == 13) ? ({mu_expr}) : {default})"
        )

    for trig_suffix in TRIGOBJ_DIAGNOSTIC_SUFFIXES:
        diagnostic_expressions[f"{lep_label}_{trig_suffix}"] = f"{lep_label}_{trig_suffix}"

    for obj_name, obj_cfg in TIGHT_OBJECT_CONFIG.items():
        for wp in obj_cfg["wps"]:
            diagnostic_expressions[f"{lep_label}_isTight{obj_name}_{wp}"] = (
                f"Alt({obj_cfg['flag_branch']}_{wp}, {lep_idx}, -999)"
            )

selected_ele_wp = globals().get("PAIR_ELE_WP", PAIR_ID_CONFIG["eleWP"])
selected_mu_wp = globals().get("PAIR_MU_WP", PAIR_ID_CONFIG["muWP"])

for lep_label, lep_idx in pair_leptons:
    lep_pdgid_expr = f"abs(Alt(Lepton_pdgId, {lep_idx}, 0))"
    ele_sf_branch = f"Lepton_tightElectron_{selected_ele_wp}_TotSF"
    mu_sf_branch = f"Lepton_tightMuon_{selected_mu_wp}_TotSF"
    ele_sf_expr = f"Alt({ele_sf_branch}, {lep_idx}, 1.0)" if _has_branch(ele_sf_branch) else "1.0"
    mu_sf_expr = f"Alt({mu_sf_branch}, {lep_idx}, 1.0)" if _has_branch(mu_sf_branch) else "1.0"
    diagnostic_expressions[f"{lep_label}_selWP_TotSF"] = (
        f"({lep_pdgid_expr} == 11) ? ({ele_sf_expr})"
        + f" : (({lep_pdgid_expr} == 13) ? ({mu_sf_expr}) : 1.0)"
    )

for obj_name, obj_cfg in TIGHT_OBJECT_CONFIG.items():
    for wp in obj_cfg["wps"]:
        diagnostic_expressions[f"nTight{obj_name}_{wp}"] = (
            f"Sum((abs(Lepton_pdgId) == {obj_cfg['pdg_id']}) && ({obj_cfg['flag_branch']}_{wp} > 0.5))"
        )

JET_BRANCH_RECIPES = {
    "pt": ("CleanJet_pt", "{jet_idx}", "-999"),
    "eta": ("CleanJet_eta", "{jet_idx}", "-999"),
    "phi": ("CleanJet_phi", "{jet_idx}", "-999"),
    "genPt": ("GenJet_pt", "{clean_jet_gen_idx}", "-999"),
    "genEta": ("GenJet_eta", "{clean_jet_gen_idx}", "-999"),
    "genPhi": ("GenJet_phi", "{clean_jet_gen_idx}", "-999"),
}

for jet_idx in range(2):
    clean_jet_gen_idx = f"Alt(Jet_genJetIdx, Alt(CleanJet_jetIdx, {jet_idx}, -1), -1)"
    for suffix, (source, index_expr, default) in JET_BRANCH_RECIPES.items():
        diagnostic_expressions[f"CleanJet_{suffix}_{jet_idx}"] = (
            f"Alt({source}, {index_expr.format(jet_idx=jet_idx, clean_jet_gen_idx=clean_jet_gen_idx)}, {default})"
        )

# mkShapesRDF books one axis per variable, shared by every cut category.  The
# former category-by-category catalogue is therefore used only as a design
# input.  These presentation axes are the common result of reviewing all six
# catalogue categories and five eras, the variable definitions below, the
# analysis thresholds, and analogous Run-3 HWW/DY/WZ configurations.  Sparse
# proxy tails are folded rather than allowed to stretch plots to multi-TeV or
# non-physical scale-factor ranges.
HISTOGRAM_BINNING_CONTRACT = {}


def _axis(edges, fold=2):
    """Return a non-uniform mkShapesRDF axis and its flow policy."""
    values = [float(edge) for edge in edges]
    if len(values) < 2 or any(
        right <= left for left, right in zip(values, values[1:])
    ):
        raise ValueError(f"Invalid common histogram edges: {values!r}")
    return (values,), fold


# Use one presentation axis for both reconstructed dilepton systems.  The
# widths progress through 2, 5, 10, and 20 GeV, avoiding the former direct
# 5-to-20 GeV jump while retaining fine resolution at low pT.
_PAIR_PT_EDGES = (
    0, 2, 4, 6, 8, 10,
    15, 20, 25, 30, 35, 40,
    50, 60, 70, 80,
    100, 120,
)


_COMMON_AXES = {
    # Primary physics observables.  The presentation ranges intentionally
    # fold both tails (fold=3): values below/above the displayed range are
    # accumulated in the first/last visible bins rather than discarded.
    "Z0_mass": _axis(
        (30, 40, 60, 80, 85, 90, 95, 100, 120),
        3,
    ),
    "X_mass": _axis(
        (30, 40, 60, 80, 85, 90, 95, 100, 120),
        3,
    ),
    "m4l": _axis((60, 80, 100, 120, 140, 160, 180, 200, 250, 300, 400, 600), 3),
    "pT4l": _axis((0, 20, 40, 60, 80, 100, 150, 200, 300, 400)),
    "PuppiMET_pt": _axis((0, 10, 20, 30, 40, 50, 80, 100, 120), 3),
    "PuppiMET_significance": _axis((0, 2, 4, 6, 8, 10, 15, 20, 30, 50)),
    "PuppiMET_sumEt": _axis((0, 100, 200, 300, 500, 750, 1000, 1500, 2000, 3000)),
    "HT": _axis((0, 30, 50, 100, 150, 200, 300, 400, 600, 800)),
    "Z0_pt": _axis(_PAIR_PT_EDGES, 3),
    "X_pt": _axis(_PAIR_PT_EDGES, 3),
    "GenMET_pt": _axis((0, 20, 40, 60, 80, 100, 150, 200, 300, 400)),
    "recoil_ut": _axis((0, 20, 40, 60, 80, 100, 150, 200, 300, 400)),
    "recoil_ux": _axis((-400, -300, -200, -150, -100, -50, 0, 50, 100, 150, 200, 300, 400), 3),
    "recoil_uy": _axis((-400, -300, -200, -150, -100, -50, 0, 50, 100, 150, 200, 300, 400), 3),
    "recoil_upar": _axis((-400, -300, -200, -150, -100, -50, 0, 50, 100, 150, 200, 300, 400), 3),
    "recoil_uperp": _axis((-400, -300, -200, -150, -100, -50, 0, 50, 100, 150, 200, 300, 400), 3),
    # Ordered selected leptons share one zero-based presentation axis.  The
    # final 100--120 GeV bin includes the overflow by construction (fold=3).
    "lZ1_pt": _axis((0, 5, 10, 15, 20, 25, 30, 40, 50, 80, 100, 120), 3),
    "lZ2_pt": _axis((0, 5, 10, 15, 20, 25, 30, 40, 50, 80, 100, 120), 3),
    "lX1_pt": _axis((0, 5, 10, 15, 20, 25, 30, 40, 50, 80, 100, 120), 3),
    "lX2_pt": _axis((0, 5, 10, 15, 20, 25, 30, 40, 50, 80, 100, 120), 3),
    # Multiplicity axes stop at the requested visible values and fold any
    # larger multiplicity into the last bin.
    "nCleanJet": _axis((-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5), 3),
    "nLepton": _axis((1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5), 3),
    # Event environment and weights.
    "nPV": ((50, -0.5, 99.5), 2),
    "nvtx": ((50, -0.5, 99.5), 2),
    "rho": ((30, 0.0, 60.0), 2),
    "puWeight": _axis((0, 0.2, 0.5, 0.8, 0.9, 1, 1.1, 1.2, 1.5, 2, 3)),
}

_LEPTON_GEN_PT_AXIS = _axis((0, 10, 20, 30, 50, 75, 100, 150, 200, 300))
_TRIGGER_OBJECT_PT_AXIS = _axis((0, 10, 20, 30, 40, 50, 75, 100, 150, 200, 300))
_JET_PT_AXIS = _axis((0, 10, 20, 30, 40, 50, 70, 90, 100), 3)
_TRIGGER_SF_AXIS = _axis((0, 0.5, 0.8, 0.9, 0.95, 1, 1.05, 1.1, 1.2, 1.5, 2))
_LEPTON_SF_AXIS = _axis((0, 0.5, 0.8, 0.9, 0.95, 1, 1.05, 1.1, 1.2, 1.5, 2))
_RATIO_AXIS = _axis((0, 0.5, 0.8, 0.9, 0.95, 0.98, 1, 1.02, 1.05, 1.1, 1.2, 1.5, 2))
_EFFICIENCY_AXIS = _axis((0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0))
_QUALITY_AXES = {
    "dxy": _axis((-0.10, -0.05, -0.02, -0.01, 0, 0.01, 0.02, 0.05, 0.10), 3),
    "dz": _axis((-0.50, -0.20, -0.10, -0.05, 0, 0.05, 0.10, 0.20, 0.50), 3),
    "eInvMinusPInv": _axis((-0.20, -0.10, -0.05, -0.02, 0, 0.02, 0.05, 0.10, 0.20), 3),
    "hoe": _axis((0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.0)),
    "jetPtRelv2": _axis((0, 5, 10, 20, 30, 50, 75, 100, 150, 200)),
    "jetRelIso": _axis((-0.5, -1.0 / 3.0, -0.2, 0, 0.1, 0.2, 0.5, 1, 2, 5), 3),
    "pfRelIso03_all": _axis((0, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 1.0)),
    "promptMVA": _axis((-1, -0.8, -0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6, 0.8, 1), 3),
    "sieie": _axis((0, 0.005, 0.010, 0.015, 0.020, 0.030, 0.050, 0.10)),
    "sip3d": _axis((0, 1, 2, 3, 4, 5, 8, 10, 15, 20)),
}


def _source_axis_bounds(name, axis):
    if (
        isinstance(axis, (list, tuple))
        and len(axis) == 1
        and isinstance(axis[0], (list, tuple))
    ):
        edges = [float(edge) for edge in axis[0]]
        if len(edges) < 2:
            raise ValueError(f"{name}: invalid source edge axis {axis!r}")
        return len(edges) - 1, edges[0], edges[-1]
    if isinstance(axis, (list, tuple)) and len(axis) == 3:
        bins, low, high = int(axis[0]), float(axis[1]), float(axis[2])
        if bins < 1 or float(axis[0]) != bins or high <= low:
            raise ValueError(f"{name}: invalid source axis {axis!r}")
        return bins, low, high
    raise ValueError(f"{name}: unsupported source axis {axis!r}")


def _is_integer_axis(name, source):
    bins, low, high = _source_axis_bounds(name, source)
    unit_bins = abs((high - low) / bins - 1.0) < 1.0e-9
    return unit_bins and (
        bins <= 32
        or name.endswith("_trigObj_bits4l")
        or name.endswith("_trigObj_filterBits")
    )


def _common_histogram_axis(name, source):
    """Resolve one physics-aware axis, independent of era and cut category."""
    if name in _COMMON_AXES:
        return _COMMON_AXES[name], "explicit-physics"
    if _is_integer_axis(name, source):
        return (source, 0), "discrete-definition"

    # Scale factors and efficiencies are intentionally handled before the
    # generic suffix rules: their catalogue outliers are numerical tails, not
    # useful plot boundaries.
    if name.endswith(("_UpOverNom", "_DownOverNom")):
        return _RATIO_AXIS, "weight-ratio"
    if name.startswith("TriggerEff"):
        return _EFFICIENCY_AXIS, "efficiency"
    if name.startswith("TriggerSF"):
        return _TRIGGER_SF_AXIS, "trigger-scale-factor"
    if (
        "LeptonSF" in name
        or name.startswith(("SelectedElectronSF", "SelectedMuonSF"))
        or name.endswith("_selWP_TotSF")
    ):
        return _LEPTON_SF_AXIS, "lepton-scale-factor"
    if name in ("btagSFbc", "btagSFlight", "BTagVetoSF"):
        return _LEPTON_SF_AXIS, "btag-scale-factor"

    for suffix, axis in _QUALITY_AXES.items():
        if name.endswith(f"_{suffix}"):
            return axis, f"object-quality:{suffix}"

    if name.endswith("_trigObj_dR"):
        return _axis((0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)), "trigger-match-distance"
    if name.endswith("_trigObj_pt"):
        return _TRIGGER_OBJECT_PT_AXIS, "trigger-object-pt"
    if name.endswith("_genPt"):
        return _LEPTON_GEN_PT_AXIS, "lepton-gen-pt"
    if name.startswith("CleanJet_") and ("_pt_" in name or "_genPt_" in name):
        return _JET_PT_AXIS, "jet-pt"

    if name.startswith("dPhi_"):
        return ((8, 0.0, 3.2), 3), "absolute-delta-phi"
    if name.endswith("_phi") or "_phi_" in name:
        return ((16, -3.2, 3.2), 0), "azimuth"
    if name.startswith("dEta_"):
        return ((20, -5.0, 5.0), 3), "lepton-delta-eta"
    if name.startswith("dR_"):
        return ((20, 0.0, 5.0), 2), "lepton-delta-r"
    if name in ("Z0_eta", "X_eta"):
        return ((20, -5.0, 5.0), 3), "composite-eta"
    if name.startswith("CleanJet_") and ("_eta_" in name or "_genEta_" in name):
        return ((24, -4.7, 4.7), 3), "jet-eta"
    if name.endswith("_eta") or name.endswith("_genEta") or name.endswith("_trigObj_eta"):
        return ((24, -3.0, 3.0), 3), "lepton-eta"

    bins, low, high = _source_axis_bounds(name, source)
    if low < -1000 or high > 1000:
        raise RuntimeError(
            f"{name}: broad source range {low:g}..{high:g} has no semantic "
            "common-binning rule"
        )
    if bins > 30:
        return ((20, low, high), 0), "coarsened-definition"
    return (source, 0), "definition"


def _resolved_histogram_axis(name, default_range):
    (resolved_range, fold), strategy = _common_histogram_axis(name, default_range)
    HISTOGRAM_BINNING_CONTRACT[name] = {
        "source": default_range,
        "resolved": resolved_range,
        "fold": fold,
        "strategy": strategy,
        "category_independent": True,
        "era_independent": True,
        "shared_by_variations": True,
    }
    return resolved_range, fold


def _hist(name, bins, low, high, xaxis, expression=None):
    resolved_range, fold = _resolved_histogram_axis(name, (bins, low, high))
    variables[name] = {
        "name": expression or name,
        "range": resolved_range,
        "xaxis": xaxis,
        "fold": fold,
    }


def _hist_edges(name, edges, xaxis, expression=None):
    edge_list = sorted({float(edge) for edge in edges})
    if len(edge_list) < 2 or any(
        right <= left for left, right in zip(edge_list, edge_list[1:])
    ):
        raise ValueError(f"Invalid edge list for {name!r}")
    resolved_range, fold = _resolved_histogram_axis(name, (edge_list,))
    variables[name] = {
        "name": expression or name,
        "range": resolved_range,
        "xaxis": xaxis,
        "fold": fold,
    }


def _fine_edges(low, high, step, protected=()):
    count = int(round((high - low) / step))
    edges = [low + index * step for index in range(count + 1)]
    edges.extend(edge for edge in protected if low <= edge <= high)
    return sorted({round(float(edge), 10) for edge in edges})


def _segmented_edges(*segments, protected=()):
    """Build a fine central source grid with explicit, wider far tails."""
    edges = []
    for low, high, step in segments:
        edges.extend(_fine_edges(low, high, step))
    edges.extend(
        edge
        for edge in protected
        if segments[0][0] <= edge <= segments[-1][1]
    )
    return sorted({round(float(edge), 10) for edge in edges})


def _masked_scalar(expression, condition):
    """Return a zero-or-one-element vector for applicability-safe filling."""
    return f"maskedHistogramValue(static_cast<float>({expression}), {condition})"


# Wide, fine-near-physics source grids.  The independent campaign optimizer
# may only coarsen or trim these grids after auditing every era, process,
# category, and nuisance; the runtime configuration itself remains hard coded.
_trigger_sf_source_edges = _segmented_edges(
    (0.0, 3.0, 0.01),
    (3.0, 10.0, 0.1),
    (10.0, 100.0, 1.0),
    (100.0, 1000.0, 10.0),
    protected=(1.0,),
)
_lepton_sf_source_edges = _segmented_edges(
    (0.0, 2.0, 0.01),
    (2.0, 5.0, 0.05),
    protected=(1.0,),
)
_btag_sf_source_edges = _segmented_edges(
    (0.0, 2.0, 0.01),
    (2.0, 5.0, 0.05),
    (5.0, 10.0, 0.25),
    protected=(1.0,),
)
_pileup_source_edges = _segmented_edges(
    (0.0, 5.0, 0.02),
    (5.0, 10.0, 0.1),
    protected=(1.0,),
)


def _optional_hist_expr(*candidates, default="maskedHistogramValue(0.f, false)"):
    for candidate in candidates:
        if _has_branch(candidate):
            return candidate
    return default


_requested_histogram_profile = str(
    globals().get(
        "HISTOGRAM_PROFILE",
        os.environ.get(
            "HISTOGRAM_PROFILE",
            globals().get("HISTOGRAM_DETAIL", os.environ.get("HISTOGRAM_DETAIL", "analysis")),
        ),
    )
).lower()
# Always construct the complete supported definition set.  Activation is a
# separate final step below and can never erase or rewrite disabled binning.
_histogram_detail = "all"
_histogram_groups = {
    "core": {"core"},
    "trigger": {"core", "trigger"},
    "objects": {"core", "objects"},
    "quality": {"core", "quality"},
    "weights": {"core", "weights"},
    "all": {"core", "trigger", "objects", "quality", "weights"},
}
if _histogram_detail not in _histogram_groups:
    raise ValueError(
        "HISTOGRAM_DETAIL must be core|trigger|objects|quality|weights|all"
    )

if bool(globals().get("HISTOGRAMS", True)):
    _groups = _histogram_groups[_histogram_detail]
    if "core" in _groups:
        # Source definitions cover every selected category boundary.  The
        # common-axis resolver below replaces these fine construction ranges
        # with the physics-aware production axes shared by all categories.
        _hist_edges(
            "Z0_mass",
            _segmented_edges(
                (0.0, 200.0, 0.5),
                (200.0, 1000.0, 2.0),
                (1000.0, 5000.0, 10.0),
                protected=(12.0, 30.0, 76.1876, 91.1876, 106.1876),
            ),
            "m_{Z_{0}} [GeV]",
        )
        _hist_edges(
            "X_mass",
            _segmented_edges(
                (0.0, 200.0, 0.5),
                (200.0, 1000.0, 2.0),
                (1000.0, 5000.0, 10.0),
                protected=(4.0, 10.0, 65.0, 70.0, 75.0, 105.0),
            ),
            "m_{X} [GeV]",
            _masked_scalar("X_mass", "hasValidX"),
        )
        _hist_edges(
            "m4l",
            _segmented_edges(
                (0.0, 1000.0, 2.0),
                (1000.0, 3000.0, 10.0),
                (3000.0, 10000.0, 50.0),
                protected=(140.0,),
            ),
            "m_{4#it{l}} [GeV]",
            _masked_scalar("m4l", "hasValidX"),
        )
        _hist_edges(
            "pT4l",
            _segmented_edges(
                (0.0, 1000.0, 2.0),
                (1000.0, 3000.0, 10.0),
                (3000.0, 10000.0, 50.0),
            ),
            "p_{T}^{4#it{l}} [GeV]",
            _masked_scalar("pT4l", "hasValidX"),
        )
        _hist_edges(
            "PuppiMET_pt",
            _segmented_edges(
                (0.0, 1000.0, 2.0),
                (1000.0, 3000.0, 10.0),
                (3000.0, 10000.0, 50.0),
                protected=(20.0, 35.0),
            ),
            "p_{T}^{miss} [GeV]",
        )
        _hist_edges(
            "PuppiMET_significance",
            _segmented_edges(
                (0.0, 200.0, 1.0),
                (200.0, 1000.0, 5.0),
                (1000.0, 10000.0, 50.0),
            ),
            "#it{S}(p_{T}^{miss})",
            _masked_scalar(
                "PuppiMET_significance", "PuppiMET_significance >= 0.f"
            ),
        )
        _hist("nCleanJet", 20, -0.5, 19.5, "N_{jet}")
        _hist_edges(
            "HT",
            _segmented_edges(
                (0.0, 1000.0, 5.0),
                (1000.0, 3000.0, 10.0),
                (3000.0, 10000.0, 50.0),
            ),
            "H_{T} [GeV]",
        )
        _hist("bVeto", 2, -0.5, 1.5, "I_{b-veto}^{30}")
        _hist(
            "sumLeptonCharge", 9, -4.5, 4.5,
            "#sum_{i=1}^{4}q_{#it{l}_{i}}",
            _masked_scalar("sumLeptonCharge", "hasValidX"),
        )
        _hist("X_isSF", 2, -0.5, 1.5, "I_{X}^{SF}", _masked_scalar("X_isSF", "hasValidX"))
        _hist("dPhi_MET_Z", 64, -3.2, 3.2, "#Delta#phi(p_{T}^{miss},Z_{0})")
        _hist("dPhi_MET_X", 64, -3.2, 3.2, "#Delta#phi(p_{T}^{miss},X)", _masked_scalar("dPhi_MET_X", "hasValidX"))
        _hist("dPhi_MET_ZplusX", 64, -3.2, 3.2, "#Delta#phi(p_{T}^{miss},4#it{l})", _masked_scalar("dPhi_MET_ZplusX", "hasValidX"))
        _wide_pt_edges = _segmented_edges(
            (0.0, 1000.0, 2.0),
            (1000.0, 3000.0, 10.0),
            (3000.0, 10000.0, 50.0),
        )
        _wide_signed_edges = _segmented_edges(
            (-10000.0, -3000.0, 50.0),
            (-3000.0, -1000.0, 10.0),
            (-1000.0, 1000.0, 5.0),
            (1000.0, 3000.0, 10.0),
            (3000.0, 10000.0, 50.0),
        )
        _hist_edges("recoil_ut", _wide_pt_edges, "u_{T} [GeV]", _masked_scalar("recoil_ut", "hasValidX"))
        _hist_edges("recoil_upar", _wide_signed_edges, "u_{#parallel} [GeV]", _masked_scalar("recoil_upar", "hasValidX"))
        _hist_edges("recoil_uperp", _wide_signed_edges, "u_{#perp} [GeV]", _masked_scalar("recoil_uperp", "hasValidX"))
        _hist_edges("Z0_pt", _wide_pt_edges, "p_{T}^{Z_{0}} [GeV]")
        _hist_edges("X_pt", _wide_pt_edges, "p_{T}^{X} [GeV]", _masked_scalar("X_pt", "hasValidX"))
        # A composite pair can have very small transverse momentum, so its
        # pseudorapidity is not bounded by the individual lepton acceptance.
        # Keep a deliberately fine, wide source axis for the independent
        # flow audit and optimizer.
        _hist("Z0_eta", 400, -20.0, 20.0, "#eta_{Z_{0}}")
        _hist("X_eta", 400, -20.0, 20.0, "#eta_{X}", _masked_scalar("X_eta", "hasValidX"))
        _hist("Z0_phi", 64, -3.2, 3.2, "#phi_{Z_{0}}")
        _hist("X_phi", 64, -3.2, 3.2, "#phi_{X}", _masked_scalar("X_phi", "hasValidX"))
        _hist("phi4l", 64, -3.2, 3.2, "#phi_{4#it{l}}", _masked_scalar("phi4l", "hasValidX"))
        _hist("Z0_isEE", 2, -0.5, 1.5, "I_{Z_{0}}^{ee}")
        _hist("Z0_isMM", 2, -0.5, 1.5, "I_{Z_{0}}^{#mu#mu}")
        _hist("X_isDF", 2, -0.5, 1.5, "I_{X}^{DF}", _masked_scalar("X_isDF", "hasValidX"))
        _hist("nLepton", 14, 1.5, 15.5, "N_{#it{l}}")
    if "trigger" in _groups:
        _hist("nFiredTriggerFamilies", 7, -0.5, 6.5, "N_{fam}^{HLT}")
        _hist("nFiredHLTPaths", 12, -0.5, 11.5, "N_{path}^{HLT}")
        _hist("triggerFamilyPriority", 7, -1.5, 5.5, "c_{fam}^{HLT}")
        # hltPathPriorityCategory returns 0 (none) through 7 (Ele30).
        _hist("hltPathPriority", 8, -0.5, 7.5, "c_{path}^{HLT}")
        _hist_edges("TriggerSF_ZX", _trigger_sf_source_edges, "w_{trig}^{4#it{l}}", _masked_scalar("TriggerSF_ZX", "hasValidX"))
        _hist("TriggerSF_ZX_Valid", 2, -0.5, 1.5, "I_{trig}^{4#it{l},valid}", _masked_scalar("TriggerSF_ZX_Valid", "hasValidX"))
        _hist("trigMatchState_4l", 8, -0.5, 7.5, "c_{trig}^{4#it{l}}", _masked_scalar("trigMatchState_4l", "hasValidX"))
        _hist("Z0_trigMatchState", 8, -0.5, 7.5, "c_{trig}^{Z_{0}}")
        _hist("X_trigMatchState", 8, -0.5, 7.5, "c_{trig}^{X}", _masked_scalar("X_trigMatchState", "hasValidX"))
        _hist("lZ1_trigObj_nMatches", 6, -0.5, 5.5, "N_{trig}(#it{l}_{Z,1})")
        _hist("lZ2_trigObj_nMatches", 6, -0.5, 5.5, "N_{trig}(#it{l}_{Z,2})")
        _hist("lX1_trigObj_nMatches", 6, -0.5, 5.5, "N_{trig}(#it{l}_{X,1})", _masked_scalar("lX1_trigObj_nMatches", "hasValidX"))
        _hist("lX2_trigObj_nMatches", 6, -0.5, 5.5, "N_{trig}(#it{l}_{X,2})", _masked_scalar("lX2_trigObj_nMatches", "hasValidX"))
    if "objects" in _groups:
        _lepton_pt_source_edges = _fine_edges(
            0.0,
            500.0,
            1.0,
            (8.0, 10.0, 12.0, 15.0, 17.0, 20.0, 23.0, 24.0, 25.0, 30.0),
        )
        _lepton_pt_source_edges = sorted(
            set(
                _lepton_pt_source_edges
                + _fine_edges(500.0, 1000.0, 5.0)
                + _fine_edges(1000.0, 5000.0, 20.0)
            )
        )
        _hist_edges("lZ1_pt", _lepton_pt_source_edges, "p_{T}(#it{l}_{Z,1}) [GeV]", "Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f)")
        _hist_edges("lZ2_pt", _lepton_pt_source_edges, "p_{T}(#it{l}_{Z,2}) [GeV]", "Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f)")
        _hist_edges("lX1_pt", _lepton_pt_source_edges, "p_{T}(#it{l}_{X,1}) [GeV]", _masked_scalar("Alt(Lepton_pt, Alt(X_idx, 0, -1), -999.f)", "hasValidX"))
        _hist_edges("lX2_pt", _lepton_pt_source_edges, "p_{T}(#it{l}_{X,2}) [GeV]", _masked_scalar("Alt(Lepton_pt, Alt(X_idx, 1, -1), -999.f)", "hasValidX"))
        for _label, _index in (("lZ1", "Z0_idx[0]"), ("lZ2", "Z0_idx[1]"), ("lX1", "X_idx[0]"), ("lX2", "X_idx[1]")):
            _index_expr = f"Alt({_index.split('_')[0]}_idx, {_index[-2]}, -1)"
            _hist(
                f"{_label}_index",
                10,
                -1.5,
                8.5,
                f"i_{{{_label}}}",
                _masked_scalar(_index_expr, "hasValidX")
                if _label.startswith("lX")
                else _index_expr,
            )
        _hist("lZ1_eta", 60, -3.0, 3.0, "#eta_{#it{l}_{Z,1}}", "Alt(Lepton_eta, Alt(Z0_idx, 0, -1), -999.f)")
        _hist("lZ2_eta", 60, -3.0, 3.0, "#eta_{#it{l}_{Z,2}}", "Alt(Lepton_eta, Alt(Z0_idx, 1, -1), -999.f)")
        _hist("lX1_eta", 60, -3.0, 3.0, "#eta_{#it{l}_{X,1}}", _masked_scalar("Alt(Lepton_eta, Alt(X_idx, 0, -1), -999.f)", "hasValidX"))
        _hist("lX2_eta", 60, -3.0, 3.0, "#eta_{#it{l}_{X,2}}", _masked_scalar("Alt(Lepton_eta, Alt(X_idx, 1, -1), -999.f)", "hasValidX"))
        _hist("lZ1_phi", 64, -3.2, 3.2, "#phi_{#it{l}_{Z,1}}", "Alt(Lepton_phi, Alt(Z0_idx, 0, -1), -999.f)")
        _hist("lZ2_phi", 64, -3.2, 3.2, "#phi_{#it{l}_{Z,2}}", "Alt(Lepton_phi, Alt(Z0_idx, 1, -1), -999.f)")
        _hist("lX1_phi", 64, -3.2, 3.2, "#phi_{#it{l}_{X,1}}", _masked_scalar("Alt(Lepton_phi, Alt(X_idx, 0, -1), -999.f)", "hasValidX"))
        _hist("lX2_phi", 64, -3.2, 3.2, "#phi_{#it{l}_{X,2}}", _masked_scalar("Alt(Lepton_phi, Alt(X_idx, 1, -1), -999.f)", "hasValidX"))
        _hist("lZ1_flavor", 2, -0.5, 1.5, "f(#it{l}_{Z,1})", "abs(Alt(Lepton_pdgId, Alt(Z0_idx, 0, -1), 0)) == 13")
        _hist("lZ2_flavor", 2, -0.5, 1.5, "f(#it{l}_{Z,2})", "abs(Alt(Lepton_pdgId, Alt(Z0_idx, 1, -1), 0)) == 13")
        _hist("lX1_flavor", 2, -0.5, 1.5, "f(#it{l}_{X,1})", _masked_scalar("abs(Alt(Lepton_pdgId, Alt(X_idx, 0, -1), 0)) == 13", "hasValidX"))
        _hist("lX2_flavor", 2, -0.5, 1.5, "f(#it{l}_{X,2})", _masked_scalar("abs(Alt(Lepton_pdgId, Alt(X_idx, 1, -1), 0)) == 13", "hasValidX"))
        _hist("nPV", 200, -0.5, 199.5, "N_{PV}", _optional_hist_expr("PV_npvs"))
        _hist("nvtx", 200, -0.5, 199.5, "N_{PV}^{good}", _optional_hist_expr("PV_npvsGood", default="maskedHistogramValue(0.f, false)"))
        _hist("rho", 100, 0.0, 100.0, "#rho", _optional_hist_expr("Rho_fixedGridRhoFastjetCentralCalo", "Rho_fixedGridRhoFastjetCentralChargedPileUp"))
    if "weights" in _groups:
        _hist_edges("SelectedLeptonSF_ZX", _lepton_sf_source_edges, "w_{#it{l}}^{4#it{l}}", _masked_scalar("SelectedLeptonSF_ZX", "hasValidX"))
        _hist("TriggerEff_ZX", 120, 0.0, 1.2, "#epsilon_{trig}^{4#it{l},data}", _masked_scalar("TriggerEff_ZX", "hasValidX"))
        _hist_edges("puWeight", _pileup_source_edges, "w_{PU}")
        # Registry completeness is independent of the active pass.  These
        # definitions remain dormant in DY-only runs and are materialized only
        # for four-lepton categories where the aliases are part of the weight
        # contract.
        _hist_edges("btagSFbc", _btag_sf_source_edges, "w_{b/c}^{b-tag}")
        _hist_edges("btagSFlight", _btag_sf_source_edges, "w_{light}^{b-tag}")
        _hist_edges("BTagVetoSF", _btag_sf_source_edges, "w_{veto}^{b-tag}")
        _hist("BTagVetoSF_Valid", 2, -0.5, 1.5, "I_{veto}^{b-tag,valid}")
        _hist("SelectedLeptonSF_ZX_UpOverNom", 100, 0.0, 2.0, "w_{#it{l}}^{up}/w_{#it{l}}", _masked_scalar("(SelectedLeptonSF_ZX_Up + (SelectedLeptonSF_ZX == 0.f)) / (SelectedLeptonSF_ZX + (SelectedLeptonSF_ZX == 0.f))", "hasValidX"))
        _hist("SelectedLeptonSF_ZX_DownOverNom", 100, 0.0, 2.0, "w_{#it{l}}^{down}/w_{#it{l}}", _masked_scalar("(SelectedLeptonSF_ZX_Down + (SelectedLeptonSF_ZX == 0.f)) / (SelectedLeptonSF_ZX + (SelectedLeptonSF_ZX == 0.f))", "hasValidX"))
        _hist_edges("TriggerSF_ZX_UpOverNom", _trigger_sf_source_edges, "w_{trig}^{up}/w_{trig}", _masked_scalar("(TriggerSF_ZX_Up + (TriggerSF_ZX == 0.f)) / (TriggerSF_ZX + (TriggerSF_ZX == 0.f))", "hasValidX"))
        _hist_edges("TriggerSF_ZX_DownOverNom", _trigger_sf_source_edges, "w_{trig}^{down}/w_{trig}", _masked_scalar("(TriggerSF_ZX_Down + (TriggerSF_ZX == 0.f)) / (TriggerSF_ZX + (TriggerSF_ZX == 0.f))", "hasValidX"))

    def _hist_missing(name, bins, low, high, xaxis, expression=None):
        if name not in variables:
            _hist(name, bins, low, high, xaxis, expression)

    def _hist_edges_missing(name, edges, xaxis, expression=None):
        if name not in variables:
            _hist_edges(name, edges, xaxis, expression)

    _lepton_tex = {
        "lZ1": "#it{l}_{Z,1}",
        "lZ2": "#it{l}_{Z,2}",
        "lX1": "#it{l}_{X,1}",
        "lX2": "#it{l}_{X,2}",
    }

    if "core" in _groups:
        _hist_missing("PuppiMET_phi", 64, -3.2, 3.2, "#phi(p_{T}^{miss})")
        _hist_edges_missing(
            "PuppiMET_sumEt",
            _segmented_edges(
                (0.0, 2000.0, 10.0),
                (2000.0, 6000.0, 25.0),
                (6000.0, 20000.0, 100.0),
            ),
            "#sum E_{T}^{PF} [GeV]",
        )
        _hist_missing("nJetInHorn", 12, -0.5, 11.5, "N_{j}^{horn}")
        for _label, _tex in _lepton_tex.items():
            _requires_x = _label.startswith("lX")
            _hist_missing(
                f"dPhi_MET_{_label}",
                64,
                -3.2,
                3.2,
                f"#Delta#phi(p_{{T}}^{{miss}},{_tex})",
                (
                    _masked_scalar(f"dPhi_MET_{_label}", "hasValidX")
                    if _requires_x
                    else None
                ),
            )
        for _lep_a, _lep_b in LEPTON_PAIR_COMBINATIONS:
            _tex_a = _lepton_tex[_lep_a]
            _tex_b = _lepton_tex[_lep_b]
            _requires_x = _lep_a.startswith("lX") or _lep_b.startswith("lX")
            _hist_missing(
                f"dPhi_{_lep_a}_{_lep_b}",
                64,
                -3.2,
                3.2,
                f"#Delta#phi({_tex_a},{_tex_b})",
                (
                    _masked_scalar(f"dPhi_{_lep_a}_{_lep_b}", "hasValidX")
                    if _requires_x
                    else None
                ),
            )
            _hist_missing(
                f"dEta_{_lep_a}_{_lep_b}",
                60,
                -6.0,
                6.0,
                f"#Delta#eta({_tex_a},{_tex_b})",
                (
                    _masked_scalar(f"dEta_{_lep_a}_{_lep_b}", "hasValidX")
                    if _requires_x
                    else None
                ),
            )
            _hist_missing(
                f"dR_{_lep_a}_{_lep_b}",
                70,
                0.0,
                7.0,
                f"#Delta R({_tex_a},{_tex_b})",
                (
                    _masked_scalar(f"dR_{_lep_a}_{_lep_b}", "hasValidX")
                    if _requires_x
                    else None
                ),
            )
        _hist_edges_missing("recoil_ux", _wide_signed_edges, "u_{x} [GeV]", _masked_scalar("recoil_ux", "hasValidX"))
        _hist_edges_missing("recoil_uy", _wide_signed_edges, "u_{y} [GeV]", _masked_scalar("recoil_uy", "hasValidX"))
        _hist_missing("X_isEE", 2, -0.5, 1.5, "I_{X}^{ee}", _masked_scalar("X_isEE", "hasValidX"))
        _hist_missing("X_isMM", 2, -0.5, 1.5, "I_{X}^{#mu#mu}", _masked_scalar("X_isMM", "hasValidX"))
        _hist_edges_missing("GenMET_pt", _wide_pt_edges, "p_{T,gen}^{miss} [GeV]", _masked_scalar("GenMET_pt", "GenMET_pt >= 0.f"))
        _hist_missing("GenMET_phi", 64, -3.2, 3.2, "#phi(p_{T,gen}^{miss})", _masked_scalar("GenMET_phi", "GenMET_pt >= 0.f"))
        for _name, _title in {
            "fifthLeptonVeto": "I_{N_{#it{l}}=4}",
            "physicalBtagVeto": "I_{b-veto}",
            "hasValidZ0": "I_{Z_{0}}^{valid}",
            "hasValidX": "I_{X}^{valid}",
            "dyLike2lBaseline": "I_{2#it{l}}^{base}",
            "fourLeptonIncremental": "I_{4#it{l}}^{base}",
        }.items():
            _hist_missing(_name, 2, -0.5, 1.5, _title)
        _hist_missing("BTagMapOverflowJetCount", 12, -0.5, 11.5, "N_{j}^{b-map,flow}")

    if "trigger" in _groups:
        for _name, _title in {
            "Trigger_ElMu": "I_{e#mu}^{HLT}",
            "Trigger_sngMu": "I_{1#mu}^{HLT}",
            "Trigger_dblMu": "I_{2#mu}^{HLT}",
            "Trigger_sngEl": "I_{1e}^{HLT}",
            "Trigger_dblEl": "I_{2e}^{HLT}",
            "Passes4lOrderedPt": "I_{p_{T}}^{4#it{l}}",
            "Passes4lOrderedPtRun2": "I_{p_{T}}^{4#it{l},R2}",
            "Passes4lOrderedPtRun3": "I_{p_{T}}^{4#it{l},R3}",
            "L2TightLeading2": "I_{L2}^{lead}",
            "L2TightLeading2Naive": "I_{L2}^{naive}",
            "L2TightProductionGate": "I_{L2}^{prod}",
            "selectedIndicesDistinct": "I_{i}^{distinct}",
            "selectedIndicesAreLeading2": "I_{i}^{lead2}",
            "selectedIndicesAreLeading4": "I_{i}^{lead4}",
            "streamPriority_MuonEG": "I_{stream}^{#mu e}",
            "streamPriority_Muon": "I_{stream}^{#mu}",
            "streamPriority_EGamma": "I_{stream}^{e/#gamma}",
        }.items():
            _hist_missing(
                _name,
                2,
                -0.5,
                1.5,
                _title,
                (
                    _masked_scalar(_name, "hasValidX")
                    if _name in ("selectedIndicesDistinct", "selectedIndicesAreLeading4")
                    else None
                ),
            )
        for _name, _title in {
            "L2TightGateIndex0": "i_{L2,1}^{prod}",
            "L2TightGateIndex1": "i_{L2,2}^{prod}",
        }.items():
            _hist_missing(_name, 10, -1.5, 8.5, _title)
        _hist_missing("dataStreamPriority", 5, -0.5, 4.5, "c_{stream}")
        _hlt_path_tex = {
            "Mu23_Ele12": "#mu23,e12",
            "Mu12_Ele23": "#mu12,e23",
            "Mu8_Ele23": "#mu8,e23",
            "Mu17_Mu8": "#mu17,#mu8",
            "IsoMu24": "#mu24",
            "Ele23_Ele12": "e23,e12",
            "Ele30": "e30",
        }
        for _path in trigger_path_branches():
            _label = TRIGGER_PATH_LABELS.get(_path, _path.replace("HLT_", ""))
            _hist_missing(
                _path,
                2,
                -0.5,
                1.5,
                f"I_{{{_hlt_path_tex.get(_label, _label)}}}^{{HLT}}",
            )
        _trig_object_specs = {
            "trigObj_idx": (12, -1.5, 10.5, "i^{trig}", ""),
            "trigObj_dR": (50, 0.0, 0.1, "#Delta R^{trig}", ""),
            "trigObj_nMatches": (6, -0.5, 5.5, "N_{match}^{trig}", ""),
            "trigObj_matchState": (9, -1.5, 7.5, "c_{match}^{trig}", ""),
            "trigObj_pt": (100, 0.0, 1000.0, "p_{T}^{trig}", " [GeV]"),
            "trigObj_eta": (60, -3.0, 3.0, "#eta^{trig}", ""),
            "trigObj_phi": (64, -3.2, 3.2, "#phi^{trig}", ""),
            "trigObj_pdgId": (27, -13.5, 13.5, "PDG^{trig}", ""),
            "trigObj_id": (27, -13.5, 13.5, "ID^{trig}", ""),
        }
        for _label, _tex in _lepton_tex.items():
            for _suffix, (_bins, _low, _high, _title, _unit) in _trig_object_specs.items():
                _is_x = _label.startswith("lX")
                if _suffix in (
                    "trigObj_dR",
                    "trigObj_pt",
                    "trigObj_eta",
                    "trigObj_phi",
                    "trigObj_pdgId",
                    "trigObj_id",
                ):
                    _trigger_expression = f"{_label}_{_suffix}_values"
                elif _is_x:
                    _trigger_expression = _masked_scalar(
                        f"{_label}_{_suffix}", "hasValidX"
                    )
                else:
                    _trigger_expression = None
                _hist_missing(
                    f"{_label}_{_suffix}",
                    _bins,
                    _low,
                    _high,
                    f"{_title}({_tex}){_unit}",
                    _trigger_expression,
                )
            _hist_missing(
                f"{_label}_trigObj_bits4l",
                128,
                -0.5,
                127.5,
                f"b_{{4#it{{l}}}}^{{trig}}({_tex})",
                (
                    _masked_scalar(f"{_label}_trigObj_bits4l", "hasValidX")
                    if _label.startswith("lX")
                    else None
                ),
            )
            for _suffix in TRIGOBJ_DIAGNOSTIC_SUFFIXES:
                if _suffix in _trig_object_specs or _suffix in (
                    "trigObj_filterBits",
                    "trigObj_bits4l",
                ):
                    continue
                _compact = _suffix.replace("trigObj_", "").replace("_", ",")
                _hist_missing(
                    f"{_label}_{_suffix}",
                    2,
                    -0.5,
                    1.5,
                    f"I_{{{_compact}}}({_tex})",
                    (
                        _masked_scalar(f"{_label}_{_suffix}", "hasValidX")
                        if _label.startswith("lX")
                        else None
                    ),
                )

    if "objects" in _groups:
        for _label, _tex in _lepton_tex.items():
            for _suffix, (_bins, _low, _high, _title) in {
                "pdgId": (27, -13.5, 13.5, "PDG"),
                "charge": (3, -1.5, 1.5, "q"),
                "genPdgId": (27, -13.5, 13.5, "PDG^{gen}"),
                "genPt": (100, 0.0, 1000.0, "p_{T}^{gen} [GeV]"),
                "genEta": (60, -3.0, 3.0, "#eta^{gen}"),
                "genPhi": (64, -3.2, 3.2, "#phi^{gen}"),
            }.items():
                _name = f"{_label}_{_suffix}"
                _hist_missing(
                    _name,
                    _bins,
                    _low,
                    _high,
                    f"{_title}({_tex})",
                    (
                        f"{_name}_values"
                        if _suffix.startswith("gen")
                        else (
                            _masked_scalar(diagnostic_expressions[_name], "hasValidX")
                            if _label.startswith("lX")
                            else diagnostic_expressions[_name]
                        )
                    ),
                )
            _name = f"{_label}_selWP_TotSF"
            _hist_edges_missing(
                _name,
                _lepton_sf_source_edges,
                f"w_{{#it{{l}}}}^{{WP}}({_tex})",
                (
                    _masked_scalar(f"{_label}_LeptonSF", "hasValidX")
                    if _label.startswith("lX")
                    else f"{_label}_LeptonSF"
                ),
            )
        for _jet in range(2):
            _jtex = f"j_{{{_jet + 1}}}"
            for _suffix, (_bins, _low, _high, _title) in {
                "pt": (100, 0.0, 1000.0, "p_{T}"),
                "eta": (100, -5.0, 5.0, "#eta"),
                "phi": (64, -3.2, 3.2, "#phi"),
                "genPt": (100, 0.0, 1000.0, "p_{T}^{gen}"),
                "genEta": (100, -5.0, 5.0, "#eta^{gen}"),
                "genPhi": (64, -3.2, 3.2, "#phi^{gen}"),
            }.items():
                _name = f"CleanJet_{_suffix}_{_jet}"
                _unit = " [GeV]" if "Pt" in _suffix or _suffix == "pt" else ""
                if _suffix in ("pt", "genPt"):
                    _hist_edges_missing(
                        _name,
                        _lepton_pt_source_edges,
                        f"{_title}({_jtex}){_unit}",
                        f"{_name}_values",
                    )
                else:
                    _hist_missing(
                        _name,
                        _bins,
                        _low,
                        _high,
                        f"{_title}({_jtex}){_unit}",
                        f"{_name}_values",
                    )

    if "quality" in _groups:
        _quality_specs = {
            "convVeto": (2, -0.5, 1.5, "I_{conv}", "", "ele"),
            "dxy": (120, -0.30, 0.30, "d_{xy}", " [cm]", None),
            "dz": (120, -0.60, 0.60, "d_{z}", " [cm]", None),
            "eInvMinusPInv": (120, -0.50, 0.50, "E^{-1}-p^{-1}", " [GeV^{-1}]", "ele"),
            "hoe": (100, 0.0, 0.50, "H/E", "", "ele"),
            "jetPtRelv2": (100, 0.0, 200.0, "p_{T}^{rel}", " [GeV]", None),
            "jetRelIso": (100, 0.0, 5.0, "I_{rel}^{j}", "", None),
            "lostHits": (8, -0.5, 7.5, "N_{hit}^{lost}", "", "ele"),
            "mvaIso_WP90": (2, -0.5, 1.5, "I_{MVA-iso}^{WP90}", "", "ele"),
            "pfIsoId": (7, -0.5, 6.5, "ID_{PF-iso}", "", "mu"),
            "pfRelIso03_all": (100, 0.0, 1.0, "I_{rel}^{#Delta R=0.3}", "", None),
            "promptMVA": (100, -1.0, 1.0, "MVA_{prompt}", "", None),
            "sieie": (100, 0.0, 0.10, "#sigma_{i#eta i#eta}", "", "ele"),
            "sip3d": (100, 0.0, 20.0, "SIP_{3D}", "", None),
            "tightId": (2, -0.5, 1.5, "I_{tight}", "", "mu"),
        }
        _quality_source_edges = {
            "dxy": _segmented_edges(
                (-500.0, -50.0, 10.0),
                (-50.0, -5.0, 1.0),
                (-5.0, -0.5, 0.1),
                (-0.5, 0.5, 0.005),
                (0.5, 5.0, 0.1),
                (5.0, 50.0, 1.0),
                (50.0, 500.0, 10.0),
                protected=(0.0,),
            ),
            "dz": _segmented_edges(
                (-1000.0, -100.0, 20.0),
                (-100.0, -10.0, 2.0),
                (-10.0, -1.0, 0.2),
                (-1.0, 1.0, 0.01),
                (1.0, 10.0, 0.2),
                (10.0, 100.0, 2.0),
                (100.0, 1000.0, 20.0),
                protected=(0.0,),
            ),
            "eInvMinusPInv": _segmented_edges(
                (-5.0, -0.5, 0.05),
                (-0.5, 0.5, 0.005),
                (0.5, 5.0, 0.05),
                protected=(0.0,),
            ),
            "hoe": _segmented_edges(
                (0.0, 0.5, 0.005),
                (0.5, 5.0, 0.05),
                (5.0, 50.0, 0.5),
            ),
            "jetPtRelv2": _segmented_edges(
                (0.0, 200.0, 1.0),
                (200.0, 500.0, 2.0),
                (500.0, 1000.0, 5.0),
            ),
            # The exact -1 no-jet sentinel is removed by aliases.py.  The
            # physical continuum down to -1/3 remains visible here.
            "jetRelIso": _segmented_edges(
                (-0.5, 0.0, 0.005),
                (0.0, 5.0, 0.02),
                (5.0, 20.0, 0.1),
                (20.0, 100.0, 0.5),
                protected=(-1.0 / 3.0, 0.0),
            ),
            "pfRelIso03_all": _segmented_edges(
                (0.0, 1.0, 0.01),
                (1.0, 5.0, 0.05),
                (5.0, 20.0, 0.25),
                (20.0, 200.0, 2.0),
            ),
            "promptMVA": _fine_edges(-1.0, 1.0, 0.01),
            "sieie": _segmented_edges(
                (0.0, 0.1, 0.001),
                (0.1, 1.0, 0.01),
                (1.0, 50.0, 0.25),
            ),
            "sip3d": _segmented_edges(
                (0.0, 20.0, 0.1),
                (20.0, 100.0, 1.0),
                (100.0, 1000.0, 10.0),
                (1000.0, 10000.0, 50.0),
            ),
        }
        for _label, _index in pair_leptons:
            _tex = _lepton_tex[_label]
            for _suffix, (_bins, _low, _high, _title, _unit, _flavor) in _quality_specs.items():
                _name = f"{_label}_{_suffix}"
                _axis_title = (
                    f"{_title}({_tex}"
                    f"{',j' if _suffix == 'jetPtRelv2' else ''}){_unit}"
                )
                if _suffix in _quality_source_edges:
                    _hist_edges_missing(
                        _name,
                        _quality_source_edges[_suffix],
                        _axis_title,
                        f"{_name}_values",
                    )
                else:
                    _hist_missing(
                        _name,
                        _bins,
                        _low,
                        _high,
                        _axis_title,
                        f"{_name}_values",
                    )
        for _obj_name, _obj_cfg in TIGHT_OBJECT_CONFIG.items():
            _short = "e" if _obj_name == "Electron" else "#mu"
            _wp_tex = {
                "wp90iso": "MVA90,iso",
                "testrecipes": "test",
                "mvaWinter22V2Iso_WP90": "MVA90",
                "mvaWinter22V2Iso_WP90_tthMVA_Run3": "MVA90+t#bar{t}H,R3",
                "mvaWinter22V2Iso_WP90_tthMVA_HWW": "MVA90+t#bar{t}H,HWW",
                "cutBased_MediumID_tthMVA_Run3": "medium+t#bar{t}H,R3",
                "cutBased_MediumID_tthMVA_HWW": "medium+t#bar{t}H,HWW",
                "cut_TightID_POG": "tight,POG",
                "cut_Tight_HWW": "tight,HWW",
                "cut_TightID_pfIsoTight_HWW_tthmva_67": "tight+PFiso+t#bar{t}H67",
                "cut_TightID_pfIsoLoose_HWW_tthmva_67": "tight+PFloose+t#bar{t}H67",
                "cut_TightID_pfIsoLoose_HWW_tthmva_HWW": "tight+PFloose+t#bar{t}H",
                "cut_TightID_pfIsoLoose_HWW_PNet": "tight+PFloose+PNet",
            }
            for _wp in _obj_cfg["wps"]:
                _compact_wp = _wp_tex.get(_wp, _wp.replace("_", ","))
                for _label, _tex in _lepton_tex.items():
                    _name = f"{_label}_isTight{_obj_name}_{_wp}"
                    _hist_missing(
                        _name,
                        2,
                        -0.5,
                        1.5,
                        f"I_{{{_short},{_compact_wp}}}({_tex})",
                        f"{_name}_values",
                    )
                _name = f"nTight{_obj_name}_{_wp}"
                _hist_missing(
                    _name,
                    10,
                    -0.5,
                    9.5,
                    f"N_{{{_short},{_compact_wp}}}^{{tight}}",
                    diagnostic_expressions[_name],
                )

    if "weights" in _groups:
        _sf_specs = {
            "TriggerSF_Z": "w_{trig}^{Z_{0}}",
            "TriggerSF_Z_Up": "w_{trig}^{Z_{0},up}",
            "TriggerSF_Z_Down": "w_{trig}^{Z_{0},down}",
            "TriggerSF_ZX_Up": "w_{trig}^{4#it{l},up}",
            "TriggerSF_ZX_Down": "w_{trig}^{4#it{l},down}",
            "TriggerSF_event": "w_{trig}^{evt}",
            "TriggerSF_event_Up": "w_{trig}^{evt,up}",
            "TriggerSF_event_Down": "w_{trig}^{evt,down}",
            "TriggerSF_selected": "w_{trig}^{sel}",
            "TriggerSF_selected_Up": "w_{trig}^{sel,up}",
            "TriggerSF_selected_Down": "w_{trig}^{sel,down}",
            "SelectedLeptonSF_Z": "w_{#it{l}}^{Z_{0}}",
            "SelectedLeptonSF_Z_Up": "w_{#it{l}}^{Z_{0},up}",
            "SelectedLeptonSF_Z_Down": "w_{#it{l}}^{Z_{0},down}",
            "SelectedLeptonSF_ZX_Up": "w_{#it{l}}^{4#it{l},up}",
            "SelectedLeptonSF_ZX_Down": "w_{#it{l}}^{4#it{l},down}",
            "SelectedElectronSF_Z_Up": "w_{e}^{Z_{0},up}",
            "SelectedElectronSF_Z_Down": "w_{e}^{Z_{0},down}",
            "SelectedMuonSF_Z_Up": "w_{#mu}^{Z_{0},up}",
            "SelectedMuonSF_Z_Down": "w_{#mu}^{Z_{0},down}",
            "SelectedElectronSF_ZX_Up": "w_{e}^{4#it{l},up}",
            "SelectedElectronSF_ZX_Down": "w_{e}^{4#it{l},down}",
            "SelectedMuonSF_ZX_Up": "w_{#mu}^{4#it{l},up}",
            "SelectedMuonSF_ZX_Down": "w_{#mu}^{4#it{l},down}",
        }
        for _name, _title in _sf_specs.items():
            _source_edges = (
                _trigger_sf_source_edges
                if _name.startswith("TriggerSF_")
                else _lepton_sf_source_edges
            )
            _hist_edges_missing(
                _name,
                _source_edges,
                _title,
                (
                    _masked_scalar(_name, "hasValidX")
                    if "ZX" in _name
                    else None
                ),
            )
        for _name, _title in {
            "TriggerSF_Z_Valid": "I_{trig}^{Z_{0},valid}",
            "TriggerSF_ZX_Valid": "I_{trig}^{4#it{l},valid}",
            "TriggerSF_event_Valid": "I_{trig}^{evt,valid}",
            "TriggerSF_selected_Valid": "I_{trig}^{sel,valid}",
        }.items():
            _hist_missing(
                _name,
                2,
                -0.5,
                1.5,
                _title,
                (
                    _masked_scalar(_name, "hasValidX")
                    if "ZX" in _name
                    else None
                ),
            )
        for _name, _title in {
            "TriggerEff_Z": "#epsilon_{trig}^{Z_{0},data}",
            "TriggerEff_ZX": "#epsilon_{trig}^{4#it{l},data}",
            "TriggerEffData_Z": "#epsilon_{trig}^{Z_{0},data}",
            "TriggerEffMC_Z": "#epsilon_{trig}^{Z_{0},MC}",
            "TriggerEffData_ZX": "#epsilon_{trig}^{4#it{l},data}",
            "TriggerEffMC_ZX": "#epsilon_{trig}^{4#it{l},MC}",
            "TriggerEffData_event": "#epsilon_{trig}^{evt,data}",
            "TriggerEffMC_event": "#epsilon_{trig}^{evt,MC}",
            "TriggerEffData_selected": "#epsilon_{trig}^{sel,data}",
            "TriggerEffMC_selected": "#epsilon_{trig}^{sel,MC}",
        }.items():
            _hist_missing(
                _name,
                120,
                0.0,
                1.2,
                _title,
                (
                    _masked_scalar(_name, "hasValidX")
                    if "ZX" in _name
                    else None
                ),
            )
        for _label, _tex in _lepton_tex.items():
            _name = f"{_label}_LeptonSF"
            _hist_edges_missing(
                _name,
                _lepton_sf_source_edges,
                f"w_{{#it{{l}}}}({_tex})",
                (
                    _masked_scalar(_name, "hasValidX")
                    if _label.startswith("lX")
                    else None
                ),
            )

    if _histogram_detail == "all":
        _missing_base_histograms = sorted(set(BASE_EVENT_BRANCHES) - set(variables))
        if _missing_base_histograms:
            raise RuntimeError(
                "HISTOGRAM_DETAIL=all is missing base variables: "
                + ", ".join(_missing_base_histograms)
            )
        if set(variables) != set(HISTOGRAM_BINNING_CONTRACT):
            raise RuntimeError("Every histogram must resolve exactly one era binning")
        if not all(
            item["shared_by_variations"]
            for item in HISTOGRAM_BINNING_CONTRACT.values()
        ):
            raise RuntimeError("Histogram axes must be shared by all variations")
        if not all(
            item["category_independent"] and item["era_independent"]
            for item in HISTOGRAM_BINNING_CONTRACT.values()
        ):
            raise RuntimeError("Histogram axes must be common to every category and era")

# The complete raw definitions above are deliberately independent of runtime
# activation.  This final materialization adds immutable registry hashes and
# resolves sparse category-variable pairs from the declarative categories.
from histogram_config import materialize_histograms

if "CATEGORY_METADATA" not in globals():
    raise RuntimeError("cuts.py/category_config.py must run before variables.py")

(
    VARIABLE_REGISTRY,
    variables,
    CATEGORY_VARIABLES,
    HISTOGRAM_PROFILE,
) = materialize_histograms(
    variables,
    HISTOGRAM_BINNING_CONTRACT,
    CATEGORY_METADATA,
    _requested_histogram_profile,
)
VARIABLE_REGISTRY_HASHES = {
    name: definition["definition_sha256"]
    for name, definition in VARIABLE_REGISTRY.items()
}
