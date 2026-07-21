import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP
if "load_selected_year" not in globals():
    _candidates = [
        globals().get("ZZCR_CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    _zzcr_config_dir = None
    for _cand in _candidates:
        if not _cand:
            continue
        _cand_abs = os.path.abspath(_cand)
        if os.path.exists(os.path.join(_cand_abs, "zzcr_year.py")):
            _zzcr_config_dir = _cand_abs
            break
    if _zzcr_config_dir is None:
        _zzcr_config_dir = os.path.abspath(os.getcwd())
    exec(
        open(os.path.join(_zzcr_config_dir, "zzcr_year.py")).read(),
        globals(),
        globals(),
    )

if (
    "PAIR_ID_CONFIG" not in globals()
    or "LEPTON_PAIR_INDEX_EXPRESSIONS" not in globals()
    or "LEPTON_PAIR_COMBINATIONS" not in globals()
    or "trigger_path_branches" not in globals()
    or "TRIGOBJ_DIAGNOSTIC_SUFFIXES" not in globals()
):
    from zzcr_selection_config import (
        EVENT_TRIGGER_DIAGNOSTIC_BRANCHES,
        LEPTON_PAIR_COMBINATIONS,
        LEPTON_PAIR_INDEX_EXPRESSIONS,
        PAIR_ID_CONFIG,
        TRIGGER_AGGREGATE_FLAGS,
        TRIGOBJ_DIAGNOSTIC_SUFFIXES,
        trigger_path_branches,
    )

variables = {}

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
    "PassesZZCR4lOrderedPt",
]

tree_branches = {branch: branch for branch in BASE_EVENT_BRANCHES}

pair_leptons = list(LEPTON_PAIR_INDEX_EXPRESSIONS.items())

def _pinned_event_branches_for_variables():
    pinned = [
        item.strip()
        for item in os.environ.get("ZZCR_PINNED_FILES", "").replace("\n", ",").split(",")
        if item.strip()
    ]
    if not pinned:
        return None
    try:
        import ROOT
    except ImportError:
        return None
    branch_sets = []
    endpoint = os.environ.get("ZZCR_XRD_READ_ENDPOINT", "root://eoscms.cern.ch").rstrip("/")
    for item in pinned:
        source = item
        if source.startswith("/store/"):
            source = f"{endpoint}/{source}"
        elif source.startswith("/eos/cms/store/") and os.environ.get("ZZCR_INPUT_ACCESS_MODE") in ("xrootd", "stage-in"):
            source = f"{endpoint}/{source[len('/eos/cms'):]}"
        try:
            fobj = ROOT.TFile.Open(source)
        except OSError:
            return None
        if not fobj or fobj.IsZombie():
            if fobj:
                fobj.Close()
            return None
        tree = fobj.Get("Events")
        if not tree:
            fobj.Close()
            return None
        branch_sets.append({branch.GetName() for branch in tree.GetListOfBranches()})
        fobj.Close()
    if not branch_sets:
        return None
    common = set(branch_sets[0])
    for branches in branch_sets[1:]:
        common &= branches
    return common


ZZCR_AVAILABLE_BRANCHES = globals().get("ZZCR_AVAILABLE_BRANCHES") or _pinned_event_branches_for_variables()


def _has_branch(branch):
    return not ZZCR_AVAILABLE_BRANCHES or branch in ZZCR_AVAILABLE_BRANCHES


def _existing_branch(branch):
    return branch if _has_branch(branch) else None


# Persist configured concrete HLT paths.  During pinned-file validation, missing
# paths become false booleans instead of invalid self-definitions.
for trigger_path_branch in trigger_path_branches():
    tree_branches[trigger_path_branch] = (
        trigger_path_branch if _has_branch(trigger_path_branch) else "false"
    )

for event_diag_branch in EVENT_TRIGGER_DIAGNOSTIC_BRANCHES:
    tree_branches[event_diag_branch] = event_diag_branch

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
    globals().get("ZZCR_ELECTRON_TIGHT_WPS")
    or ElectronWP[_L2TIGHT_ERA]["TightObjWP"].keys()
)
muon_tight_wps = list(
    globals().get("ZZCR_MUON_TIGHT_WPS") or MuonWP[_L2TIGHT_ERA]["TightObjWP"].keys()
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
    "pfRelIso04_all": {"ele": "Electron_pfRelIso04_all", "mu": "Muon_pfRelIso04_all", "default": "-999.f"},
    "promptMVA": {"ele": "Electron_promptMVA", "mu": "Muon_promptMVA", "default": "-999.f"},
    "sieie": {"ele": "Electron_sieie", "mu": None, "default": "-999.f"},
    "sip3d": {"ele": "Electron_sip3d", "mu": "Muon_sip3d", "default": "-999.f"},
    "tightId": {"ele": None, "mu": "Muon_tightId", "default": "0"},
}

for lep_label, lep_idx in pair_leptons:
    for suffix, source in LEPTON_BRANCH_RECIPES.items():
        if _existing_branch(source):
            tree_branches[f"{lep_label}_{suffix}"] = f"Alt({source}, {lep_idx}, -999)"
        else:
            tree_branches[f"{lep_label}_{suffix}"] = "-999"


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
        tree_branches[f"{lep_label}_{suffix}"] = (
            f"({lep_pdgid_expr} == 11) ? ({ele_expr}) : (({lep_pdgid_expr} == 13) ? ({mu_expr}) : {default})"
        )

    for trig_suffix in TRIGOBJ_DIAGNOSTIC_SUFFIXES:
        tree_branches[f"{lep_label}_{trig_suffix}"] = f"{lep_label}_{trig_suffix}"

    for obj_name, obj_cfg in TIGHT_OBJECT_CONFIG.items():
        for wp in obj_cfg["wps"]:
            tree_branches[f"{lep_label}_isTight{obj_name}_{wp}"] = (
                f"Alt({obj_cfg['flag_branch']}_{wp}, {lep_idx}, -999)"
            )

selected_ele_wp = globals().get("ZZCR_PAIR_ELE_WP", PAIR_ID_CONFIG["eleWP"])
selected_mu_wp = globals().get("ZZCR_PAIR_MU_WP", PAIR_ID_CONFIG["muWP"])

for lep_label, lep_idx in pair_leptons:
    lep_pdgid_expr = f"abs(Alt(Lepton_pdgId, {lep_idx}, 0))"
    ele_sf_branch = f"Lepton_tightElectron_{selected_ele_wp}_TotSF"
    mu_sf_branch = f"Lepton_tightMuon_{selected_mu_wp}_TotSF"
    ele_sf_expr = f"Alt({ele_sf_branch}, {lep_idx}, 1.0)" if _has_branch(ele_sf_branch) else "1.0"
    mu_sf_expr = f"Alt({mu_sf_branch}, {lep_idx}, 1.0)" if _has_branch(mu_sf_branch) else "1.0"
    tree_branches[f"{lep_label}_selWP_TotSF"] = (
        f"({lep_pdgid_expr} == 11) ? ({ele_sf_expr})"
        + f" : (({lep_pdgid_expr} == 13) ? ({mu_sf_expr}) : 1.0)"
    )

for obj_name, obj_cfg in TIGHT_OBJECT_CONFIG.items():
    for wp in obj_cfg["wps"]:
        tree_branches[f"nTight{obj_name}_{wp}"] = (
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
        tree_branches[f"CleanJet_{suffix}_{jet_idx}"] = (
            f"Alt({source}, {index_expr.format(jet_idx=jet_idx, clean_jet_gen_idx=clean_jet_gen_idx)}, {default})"
        )

# Convert extra variable defs into tree branches.
for var_name, var_def in variables.items():
    if "tree" in var_def:
        continue

    exprs = [e.strip() for e in var_def["name"].split(":")]

    if len(exprs) == 1:
        tree_branches[var_name] = exprs[0]
    else:
        for i, expr in enumerate(exprs):
            tree_branches[f"{var_name}_{i}"] = expr

variables["tree"] = {
    "tree": tree_branches,
    "cuts": ["zz_cr"],
}
