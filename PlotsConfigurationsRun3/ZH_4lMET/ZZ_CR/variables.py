variables = {}

tree_branches = {
    # Event-level observables
    "nCleanJet": "nCleanJet",
    "Z0_mass": "Z0_mass",
    "Z0_pt": "Z0_pt",
    "X_mass": "X_mass",
    "X_pt": "X_pt",
    "m4l": "m4l",
    "pT4l": "pT4l",
    "PuppiMET_pt": "PuppiMET_pt",
    "PuppiMET_phi": "PuppiMET_phi",
    "HT": "HT",
    "sumLeptonCharge": "sumLeptonCharge",
    "Z0_isEE": "Z0_isEE",
    "Z0_isMM": "Z0_isMM",
    "X_isEE": "X_isEE",
    "X_isMM": "X_isMM",
    "GenMET_pt": "GenMET_pt",
    "GenMET_phi": "GenMET_phi",
    "bVeto": "bVeto",
    # Leading jets
    "CleanJet_pt_0": "Alt(CleanJet_pt, 0, 0)",
    "CleanJet_pt_1": "Alt(CleanJet_pt, 1, 0)",
    "CleanJet_eta_0": "Alt(CleanJet_eta, 0, 0)",
    "CleanJet_eta_1": "Alt(CleanJet_eta, 1, 0)",
    "CleanJet_phi_0": "Alt(CleanJet_phi, 0, 0)",
    "CleanJet_phi_1": "Alt(CleanJet_phi, 1, 0)",
}

pair_leptons = [
    ("lZ1", "Alt(Z0_idx, 0, -1)"),
    ("lZ2", "Alt(Z0_idx, 1, -1)"),
    ("lX1", "Alt(X_idx, 0, -1)"),
    ("lX2", "Alt(X_idx, 1, -1)"),
]

for lep_label, lep_idx in pair_leptons:
    tree_branches[f"{lep_label}_pt"] = f"Alt(Lepton_pt, {lep_idx}, 0)"
    tree_branches[f"{lep_label}_eta"] = f"Alt(Lepton_eta, {lep_idx}, 0)"
    tree_branches[f"{lep_label}_phi"] = f"Alt(Lepton_phi, {lep_idx}, 0)"
    tree_branches[f"{lep_label}_pdgId"] = f"Alt(Lepton_pdgId, {lep_idx}, 0)"
    tree_branches[f"{lep_label}_charge"] = (
        f"Alt((Lepton_pdgId < 0) - (Lepton_pdgId > 0), {lep_idx}, 0)"
    )

for i in range(2):
    clean_jet_gen_idx = f"Alt(Jet_genJetIdx, Alt(CleanJet_jetIdx, {i}, -1), -1)"
    tree_branches[f"CleanJet_genPt_{i}"] = f"Alt(GenJet_pt, {clean_jet_gen_idx}, -999)"
    tree_branches[f"CleanJet_genEta_{i}"] = f"Alt(GenJet_eta, {clean_jet_gen_idx}, 0)"
    tree_branches[f"CleanJet_genPhi_{i}"] = f"Alt(GenJet_phi, {clean_jet_gen_idx}, 0)"

# Keep variable-to-branch conversion in place for compatibility with potential
# local additions to `variables`.
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

for wp in electron_tight_wps_2022:
    tree_branches[f"nTightElectron_{wp}"] = (
        f"Sum((abs(Lepton_pdgId) == 11) && (Lepton_isTightElectron_{wp} > 0.5))"
    )

for wp in muon_tight_wps_2022:
    tree_branches[f"nTightMuon_{wp}"] = (
        f"Sum((abs(Lepton_pdgId) == 13) && (Lepton_isTightMuon_{wp} > 0.5))"
    )

for lep_label, lep_idx in pair_leptons:
    for wp in electron_tight_wps_2022:
        tree_branches[f"{lep_label}_isTightElectron_{wp}"] = (
            f"Alt(Lepton_isTightElectron_{wp}, {lep_idx}, 0)"
        )

    for wp in muon_tight_wps_2022:
        tree_branches[f"{lep_label}_isTightMuon_{wp}"] = (
            f"Alt(Lepton_isTightMuon_{wp}, {lep_idx}, 0)"
        )

    tree_branches[f"{lep_label}_genPdgId"] = f"Alt(Lepton_genPdgId, {lep_idx}, 0)"
    tree_branches[f"{lep_label}_genPt"] = f"Alt(Lepton_genPt, {lep_idx}, 0)"
    tree_branches[f"{lep_label}_genEta"] = f"Alt(Lepton_genEta, {lep_idx}, 0)"
    tree_branches[f"{lep_label}_genPhi"] = f"Alt(Lepton_genPhi, {lep_idx}, 0)"

variables["tree"] = {
    "tree": tree_branches,
    "cuts": ["zz_cr"],
}
