variables = {}

variables["nLepton"] = {
    "name": "nLepton",
    "range": (6, 0, 6),
    "xaxis": "nLepton",
    "fold": 3,
}

variables["nCleanJet"] = {
    "name": "nCleanJet",
    "range": (6, 0, 6),
    "xaxis": "nCleanJet",
    "fold": 3,
}

variables["nElectron"] = {
    "name": "Sum(abs(Lepton_pdgId) == 11)",
    "range": (5, 0, 5),
    "xaxis": "nElectron",
    "fold": 3,
}

variables["nMuon"] = {
    "name": "Sum(abs(Lepton_pdgId) == 13)",
    "range": (5, 0, 5),
    "xaxis": "nMuon",
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

variables["Lepton_pt_0"] = {
    "name": "Alt(Lepton_pt, 0, 0)",
    "range": (30, 0, 150),
    "xaxis": "p_{T}^{l1} [GeV]",
    "fold": 3,
}

variables["Lepton_pt_1"] = {
    "name": "Alt(Lepton_pt, 1, 0)",
    "range": (30, 0, 150),
    "xaxis": "p_{T}^{l2} [GeV]",
    "fold": 3,
}

variables["Lepton_pt_2"] = {
    "name": "Alt(Lepton_pt, 2, 0)",
    "range": (30, 0, 100),
    "xaxis": "p_{T}^{l3} [GeV]",
    "fold": 3,
}

variables["Lepton_pt_3"] = {
    "name": "Alt(Lepton_pt, 3, 0)",
    "range": (30, 0, 100),
    "xaxis": "p_{T}^{l4} [GeV]",
    "fold": 3,
}

variables["Lepton_eta_0"] = {
    "name": "Alt(Lepton_eta, 0, 0)",
    "range": (30, -3.0, 3.0),
    "xaxis": "#eta^{l1}",
    "fold": 3,
}

variables["Lepton_eta_1"] = {
    "name": "Alt(Lepton_eta, 1, 0)",
    "range": (30, -3.0, 3.0),
    "xaxis": "#eta^{l2}",
    "fold": 3,
}

variables["Lepton_eta_2"] = {
    "name": "Alt(Lepton_eta, 2, 0)",
    "range": (30, -3.0, 3.0),
    "xaxis": "#eta^{l3}",
    "fold": 3,
}

variables["Lepton_eta_3"] = {
    "name": "Alt(Lepton_eta, 3, 0)",
    "range": (30, -3.0, 3.0),
    "xaxis": "#eta^{l4}",
    "fold": 3,
}

variables["Lepton_phi_0"] = {
    "name": "Alt(Lepton_phi, 0, 0)",
    "range": (32, -3.2, 3.2),
    "xaxis": "#phi^{l1}",
    "fold": 3,
}

variables["Lepton_phi_1"] = {
    "name": "Alt(Lepton_phi, 1, 0)",
    "range": (32, -3.2, 3.2),
    "xaxis": "#phi^{l2}",
    "fold": 3,
}

variables["Lepton_phi_2"] = {
    "name": "Alt(Lepton_phi, 2, 0)",
    "range": (32, -3.2, 3.2),
    "xaxis": "#phi^{l3}",
    "fold": 3,
}

variables["Lepton_phi_3"] = {
    "name": "Alt(Lepton_phi, 3, 0)",
    "range": (32, -3.2, 3.2),
    "xaxis": "#phi^{l4}",
    "fold": 3,
}

variables["Lepton_pdgId_0"] = {
    "name": "Alt(Lepton_pdgId, 0, 0)",
    "range": (27, -13.5, 13.5),
    "xaxis": "pdgId^{l1}",
    "fold": 0,
}

variables["Lepton_pdgId_1"] = {
    "name": "Alt(Lepton_pdgId, 1, 0)",
    "range": (27, -13.5, 13.5),
    "xaxis": "pdgId^{l2}",
    "fold": 0,
}

variables["Lepton_pdgId_2"] = {
    "name": "Alt(Lepton_pdgId, 2, 0)",
    "range": (27, -13.5, 13.5),
    "xaxis": "pdgId^{l3}",
    "fold": 0,
}

variables["Lepton_pdgId_3"] = {
    "name": "Alt(Lepton_pdgId, 3, 0)",
    "range": (27, -13.5, 13.5),
    "xaxis": "pdgId^{l4}",
    "fold": 0,
}

variables["Lepton_charge_0"] = {
    "name": "Alt(Lepton_charge, 0, 0)",
    "range": (5, -2.5, 2.5),
    "xaxis": "q^{l1}",
    "fold": 0,
}

variables["Lepton_charge_1"] = {
    "name": "Alt(Lepton_charge, 1, 0)",
    "range": (5, -2.5, 2.5),
    "xaxis": "q^{l2}",
    "fold": 0,
}

variables["Lepton_charge_2"] = {
    "name": "Alt(Lepton_charge, 2, 0)",
    "range": (5, -2.5, 2.5),
    "xaxis": "q^{l3}",
    "fold": 0,
}

variables["Lepton_charge_3"] = {
    "name": "Alt(Lepton_charge, 3, 0)",
    "range": (5, -2.5, 2.5),
    "xaxis": "q^{l4}",
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
