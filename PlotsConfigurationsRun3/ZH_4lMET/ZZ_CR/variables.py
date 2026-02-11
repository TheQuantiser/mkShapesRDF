variables = {}

variables["nCleanJet"] = {
    "name": "nCleanJet",
    "range": (6, 0, 6),
    "xaxis": "nCleanJet",
    "fold": 3,
}

variables["Z0_mass"] = {
    "name": "Z0_mass",
    "range": (40, 40, 120),
    "xaxis": "m_{Z0} [GeV]",
    "fold": 3,
}

variables["Z0_pt"] = {
    "name": "Z0_pt",
    "range": (30, 0, 150),
    "xaxis": "p_{T}^{Z0} [GeV]",
    "fold": 3,
}

variables["X_mass"] = {
    "name": "X_mass",
    "range": (40, 0, 200),
    "xaxis": "m_{X} [GeV]",
    "fold": 3,
}

variables["X_pt"] = {
    "name": "X_pt",
    "range": (30, 0, 150),
    "xaxis": "p_{T}^{X} [GeV]",
    "fold": 3,
}

variables["m4l"] = {
    "name": "m4l",
    "range": (40, 0, 400),
    "xaxis": "m_{4l} [GeV]",
    "fold": 3,
}

variables["pT4l"] = {
    "name": "pT4l",
    "range": (30, 0, 200),
    "xaxis": "p_{T}^{4l} [GeV]",
    "fold": 3,
}

variables["PuppiMET_pt"] = {
    "name": "PuppiMET_pt",
    "range": (30, 0, 60),
    "xaxis": "PuppiMET p_{T} [GeV]",
    "fold": 3,
}

variables["PuppiMET_phi"] = {
    "name": "PuppiMET_phi",
    "range": (32, -3.2, 3.2),
    "xaxis": "PuppiMET #phi",
    "fold": 3,
}

variables["HT"] = {
    "name": "HT",
    "range": (40, 0, 400),
    "xaxis": "H_{T} [GeV]",
    "fold": 3,
}

pair_leptons = [
    ("lZ1", "Alt(Z0_idx, 0, -1)"),
    ("lZ2", "Alt(Z0_idx, 1, -1)"),
    ("lX1", "Alt(X_idx, 0, -1)"),
    ("lX2", "Alt(X_idx, 1, -1)"),
]

for lep_label, lep_idx in pair_leptons:
    variables[f"{lep_label}_pt"] = {
        "name": f"Alt(Lepton_pt, {lep_idx}, 0)",
        "range": (30, 0, 150),
        "xaxis": f"p_{{T}}^{{{lep_label}}} [GeV]",
        "fold": 3,
    }

    variables[f"{lep_label}_eta"] = {
        "name": f"Alt(Lepton_eta, {lep_idx}, 0)",
        "range": (30, -3.0, 3.0),
        "xaxis": f"#eta^{{{lep_label}}}",
        "fold": 3,
    }

    variables[f"{lep_label}_phi"] = {
        "name": f"Alt(Lepton_phi, {lep_idx}, 0)",
        "range": (32, -3.2, 3.2),
        "xaxis": f"#phi^{{{lep_label}}}",
        "fold": 3,
    }

    variables[f"{lep_label}_pdgId"] = {
        "name": f"Alt(Lepton_pdgId, {lep_idx}, 0)",
        "range": (27, -13.5, 13.5),
        "xaxis": f"pdgId^{{{lep_label}}}",
        "fold": 0,
    }

    variables[f"{lep_label}_charge"] = {
        "name": f"Alt((Lepton_pdgId < 0) - (Lepton_pdgId > 0), {lep_idx}, 0)",
        "range": (5, -2.5, 2.5),
        "xaxis": f"q^{{{lep_label}}}",
        "fold": 0,
    }

variables["sumLeptonCharge"] = {
    "name": "sumLeptonCharge",
    "range": (9, -4.5, 4.5),
    "xaxis": "#Sigma q_{l}",
    "fold": 3,
}

variables["Z0_isEE"] = {
    "name": "Z0_isEE",
    "range": (2, 0, 2),
    "xaxis": "Z0 is ee",
    "fold": 3,
}

variables["Z0_isMM"] = {
    "name": "Z0_isMM",
    "range": (2, 0, 2),
    "xaxis": "Z0 is #mu#mu",
    "fold": 3,
}

variables["X_isEE"] = {
    "name": "X_isEE",
    "range": (2, 0, 2),
    "xaxis": "X is ee",
    "fold": 3,
}

variables["X_isMM"] = {
    "name": "X_isMM",
    "range": (2, 0, 2),
    "xaxis": "X is #mu#mu",
    "fold": 3,
}

variables["CleanJet_pt_0"] = {
    "name": "Alt(CleanJet_pt, 0, 0)",
    "range": (30, 0, 200),
    "xaxis": "p_{T}^{j1} [GeV]",
    "fold": 3,
}

variables["CleanJet_pt_1"] = {
    "name": "Alt(CleanJet_pt, 1, 0)",
    "range": (30, 0, 200),
    "xaxis": "p_{T}^{j2} [GeV]",
    "fold": 3,
}

variables["CleanJet_eta_0"] = {
    "name": "Alt(CleanJet_eta, 0, 0)",
    "range": (30, -5.0, 5.0),
    "xaxis": "#eta^{j1}",
    "fold": 3,
}

variables["CleanJet_eta_1"] = {
    "name": "Alt(CleanJet_eta, 1, 0)",
    "range": (30, -5.0, 5.0),
    "xaxis": "#eta^{j2}",
    "fold": 3,
}

variables["CleanJet_phi_0"] = {
    "name": "Alt(CleanJet_phi, 0, 0)",
    "range": (32, -3.2, 3.2),
    "xaxis": "#phi^{j1}",
    "fold": 3,
}

variables["CleanJet_phi_1"] = {
    "name": "Alt(CleanJet_phi, 1, 0)",
    "range": (32, -3.2, 3.2),
    "xaxis": "#phi^{j2}",
    "fold": 3,
}

tree_branches = {}

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


for lep_label, lepton_index in pair_leptons:
    tree_branches[f"{lep_label}_pt"] = f"Alt(Lepton_pt, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_eta"] = f"Alt(Lepton_eta, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_phi"] = f"Alt(Lepton_phi, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_pdgId"] = f"Alt(Lepton_pdgId, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_charge"] = f"Alt((Lepton_pdgId < 0) - (Lepton_pdgId > 0), {lepton_index}, 0)"


for lep_label, lepton_index in pair_leptons:
    tree_branches[f"{lep_label}_pt"] = f"Alt(Lepton_pt, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_eta"] = f"Alt(Lepton_eta, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_phi"] = f"Alt(Lepton_phi, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_pdgId"] = f"Alt(Lepton_pdgId, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_charge"] = f"Alt((Lepton_pdgId < 0) - (Lepton_pdgId > 0), {lepton_index}, 0)"

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
    variables[f"nTightElectron_{wp}"] = {
        "name": f"Sum((abs(Lepton_pdgId) == 11) && (Lepton_isTightElectron_{wp} > 0.5))",
        "range": (5, 0, 5),
        "xaxis": f"N_{{e}} passing {wp}",
        "fold": 3,
    }

for wp in muon_tight_wps_2022:
    variables[f"nTightMuon_{wp}"] = {
        "name": f"Sum((abs(Lepton_pdgId) == 13) && (Lepton_isTightMuon_{wp} > 0.5))",
        "range": (5, 0, 5),
        "xaxis": f"N_{{#mu}} passing {wp}",
        "fold": 3,
    }

for lep_label, lepton_index in pair_leptons:
    for wp in electron_tight_wps_2022:
        tree_branches[f"{lep_label}_isTightElectron_{wp}"] = (
            f"Alt(Lepton_isTightElectron_{wp}, {lepton_index}, 0)"
        )
    for wp in muon_tight_wps_2022:
        tree_branches[f"{lep_label}_isTightMuon_{wp}"] = (
            f"Alt(Lepton_isTightMuon_{wp}, {lepton_index}, 0)"
        )
    tree_branches[f"{lep_label}_genPdgId"] = f"Alt(Lepton_genPdgId, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_genPt"] = f"Alt(Lepton_genPt, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_genEta"] = f"Alt(Lepton_genEta, {lepton_index}, 0)"
    tree_branches[f"{lep_label}_genPhi"] = f"Alt(Lepton_genPhi, {lepton_index}, 0)"

for wp in electron_tight_wps_2022:
    tree_branches[f"nTightElectron_{wp}"] = (
        f"Sum((abs(Lepton_pdgId) == 11) && (Lepton_isTightElectron_{wp} > 0.5))"
    )

for wp in muon_tight_wps_2022:
    tree_branches[f"nTightMuon_{wp}"] = (
        f"Sum((abs(Lepton_pdgId) == 13) && (Lepton_isTightMuon_{wp} > 0.5))"
    )

tree_branches["GenMET_pt"] = "GenMET_pt"
tree_branches["GenMET_phi"] = "GenMET_phi"

variables["tree"] = {
    "tree": tree_branches,
    "cuts": ["zz_cr"],
}
