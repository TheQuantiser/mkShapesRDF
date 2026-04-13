from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP

from zzcr_year import load_selected_year

if (
    "PAIR_ID_CONFIG" not in globals()
    or "LEPTON_PAIR_INDEX_EXPRESSIONS" not in globals()
    or "LEPTON_PAIR_COMBINATIONS" not in globals()
):
    from zzcr_selection_config import LEPTON_PAIR_COMBINATIONS, LEPTON_PAIR_INDEX_EXPRESSIONS, PAIR_ID_CONFIG

variables = {}

BASE_EVENT_BRANCHES = [

    "Trigger_ElMu",
    "Trigger_sngMu",
    "Trigger_dblMu",
    "Trigger_sngEl",
    "Trigger_dblEl",

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
    "GenMET_pt",
    "GenMET_phi",
    "bVeto",
    "PassesZZCR4lOrderedPt",
]

tree_branches = {branch: branch for branch in BASE_EVENT_BRANCHES}

pair_leptons = list(LEPTON_PAIR_INDEX_EXPRESSIONS.items())

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
electron_tight_wps = list(ElectronWP[_L2TIGHT_ERA]["TightObjWP"].keys())
muon_tight_wps = list(MuonWP[_L2TIGHT_ERA]["TightObjWP"].keys())

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

for lep_label, lep_idx in pair_leptons:
    for suffix, source in LEPTON_BRANCH_RECIPES.items():
        tree_branches[f"{lep_label}_{suffix}"] = f"Alt({source}, {lep_idx}, -999)"

    for trig_suffix in (
        "trigObj_pt",
        "trigObj_eta",
        "trigObj_phi",
        "trigObj_pdgId",
        "trigObj_filterBits",
        "trigObj_bits4l",
    ):
        tree_branches[f"{lep_label}_{trig_suffix}"] = f"{lep_label}_{trig_suffix}"

    for obj_name, obj_cfg in TIGHT_OBJECT_CONFIG.items():
        for wp in obj_cfg["wps"]:
            tree_branches[f"{lep_label}_isTight{obj_name}_{wp}"] = (
                f"Alt({obj_cfg['flag_branch']}_{wp}, {lep_idx}, -999)"
            )

selected_ele_wp = PAIR_ID_CONFIG["eleWP"]
selected_mu_wp = PAIR_ID_CONFIG["muWP"]

for lep_label, lep_idx in pair_leptons:
    lep_pdgid_expr = f"abs(Alt(Lepton_pdgId, {lep_idx}, 0))"
    tree_branches[f"{lep_label}_selWP_TotSF"] = (
        f"({lep_pdgid_expr} == 11) ? Alt(Lepton_tightElectron_{selected_ele_wp}_TotSF, {lep_idx}, 1.0)"
        + f" : (({lep_pdgid_expr} == 13) ? Alt(Lepton_tightMuon_{selected_mu_wp}_TotSF, {lep_idx}, 1.0) : 1.0)"
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
