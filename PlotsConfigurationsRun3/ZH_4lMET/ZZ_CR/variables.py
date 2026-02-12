variables = {}

BASE_EVENT_BRANCHES = [
    "nCleanJet",
    "Z0_mass",
    "Z0_pt",
    "X_mass",
    "X_pt",
    "m4l",
    "pT4l",
    "PuppiMET_pt",
    "PuppiMET_phi",
    "HT",
    "sumLeptonCharge",
    "Z0_isEE",
    "Z0_isMM",
    "X_isEE",
    "X_isMM",
    "GenMET_pt",
    "GenMET_phi",
    "bVeto",
]

tree_branches = {branch: branch for branch in BASE_EVENT_BRANCHES}

pair_leptons = [
    ("lZ1", "Alt(Z0_idx, 0, -1)"),
    ("lZ2", "Alt(Z0_idx, 1, -1)"),
    ("lX1", "Alt(X_idx, 0, -1)"),
    ("lX2", "Alt(X_idx, 1, -1)"),
]

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

electron_tight_wps_2022 = [
    "testrecipes",
    "wp90iso",
    "mvaWinter22V2Iso_WP90",
    "cutBased_LooseID_tthMVA_Run3",
    "cutBased_LooseID_tthMVA_HWW",
]

muon_tight_wps_2022 = [
    "cut_TightID_POG",
    "cut_Tight_HWW",
    "cut_TightID_pfIsoTight_HWW_tthmva_67",
    "cut_TightID_pfIsoLoose_HWW_tthmva_67",
    "cut_TightID_pfIsoLoose_HWW_tthmva_HWW",
]

TIGHT_OBJECT_CONFIG = {
    "Electron": {
        "pdg_id": 11,
        "wps": electron_tight_wps_2022,
        "flag_branch": "Lepton_isTightElectron",
    },
    "Muon": {
        "pdg_id": 13,
        "wps": muon_tight_wps_2022,
        "flag_branch": "Lepton_isTightMuon",
    },
}

for lep_label, lep_idx in pair_leptons:
    for suffix, source in LEPTON_BRANCH_RECIPES.items():
        tree_branches[f"{lep_label}_{suffix}"] = f"Alt({source}, {lep_idx}, 0)"

    for obj_name, obj_cfg in TIGHT_OBJECT_CONFIG.items():
        for wp in obj_cfg["wps"]:
            tree_branches[f"{lep_label}_isTight{obj_name}_{wp}"] = (
                f"Alt({obj_cfg['flag_branch']}_{wp}, {lep_idx}, 0)"
            )

for obj_name, obj_cfg in TIGHT_OBJECT_CONFIG.items():
    for wp in obj_cfg["wps"]:
        tree_branches[f"nTight{obj_name}_{wp}"] = (
            f"Sum((abs(Lepton_pdgId) == {obj_cfg['pdg_id']}) && ({obj_cfg['flag_branch']}_{wp} > 0.5))"
        )

JET_BRANCH_RECIPES = {
    "pt": ("CleanJet_pt", "{jet_idx}", "0"),
    "eta": ("CleanJet_eta", "{jet_idx}", "0"),
    "phi": ("CleanJet_phi", "{jet_idx}", "0"),
    "genPt": ("GenJet_pt", "{clean_jet_gen_idx}", "-999"),
    "genEta": ("GenJet_eta", "{clean_jet_gen_idx}", "0"),
    "genPhi": ("GenJet_phi", "{clean_jet_gen_idx}", "0"),
}

for jet_idx in range(2):
    clean_jet_gen_idx = f"Alt(Jet_genJetIdx, Alt(CleanJet_jetIdx, {jet_idx}, -1), -1)"
    for suffix, (source, index_expr, default) in JET_BRANCH_RECIPES.items():
        tree_branches[f"CleanJet_{suffix}_{jet_idx}"] = (
            f"Alt({source}, {index_expr.format(jet_idx=jet_idx, clean_jet_gen_idx=clean_jet_gen_idx)}, {default})"
        )

# Variable-to-branch conversion
for var_name, var_def in variables.items():
    if "tree" in var_def:
        continue

    exprs = [e.strip() for e in var_def["name"].split(":")]

    if len(exprs) == 1:
        # one output branch: <var_name> = <expression>
        tree_branches[var_name] = exprs[0]
    else:
        # multiple output branches: <var_name>_<i> = <expr_i>
        for i, expr in enumerate(exprs):
            tree_branches[f"{var_name}_{i}"] = expr

variables["tree"] = {
    "tree": tree_branches,
    "cuts": ["zz_cr"],
}